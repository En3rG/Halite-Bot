import copy
import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import MyBotDirections as DIR
import logging
from collections import namedtuple, OrderedDict
import MyBotAttack as ATK
import MyBotExpand as EXP
import MyBotEvade as EV
import MyBotFunctions as FUNC


################################################################################
#####May possibly combine two units and go over 255 when pushed back, but this is better than losing a 255 in the battle
#####less probability of this occuring
################################################################################
def manageOverStrengthPushed(PARAMS,GLOBALVARS):
    for keyID, mySquaresDict in PARAMS.allMySquares.items():
        #####take squares going to the first square pushed into account
        if mySquaresDict['pushedForEvadingNum'] == 1:
            PARAMS.managedTargetIDs.append(keyID)
            origSquare = mySquaresDict['currentsquare']
            origSquareID = FUNC.getID(origSquare)
            neighbors = GLOBALVARS.game_map.neighbors(origSquare, n=1, include_self=False)

            for neighbor in neighbors:
                neighborID = FUNC.getID(neighbor)
                isTargetMine = FUNC.getIsTargetMine(PARAMS, neighborID)
                if isTargetMine == True:
                    neighborTargetSquare = GLOBALVARS.game_map.get_target(neighbor,PARAMS.allMySquares[neighborID]['direction'])
                    neighborTargetSquareID = FUNC.getID(neighborTargetSquare)

                    if neighborTargetSquareID == origSquareID:
                        #####same target
                        PARAMS.allMySquares[neighborID]['direction'] = STILL

        #####take other squares pushed into account
        if mySquaresDict['pushedForEvading'] == True:
            origSquare = mySquaresDict['currentsquare']
            origSquareID = keyID
            origTargetSquare = GLOBALVARS.game_map.get_target(origSquare,mySquaresDict['direction'])
            origTargetID = FUNC.getID(origTargetSquare)
            totalStrength = origSquare.strength
            PARAMS.managedTargetIDs.append(origTargetID)
            #####check neighbors of target, see if any has same target as origTargetSquare
            targetNeighbors = GLOBALVARS.game_map.neighbors(origTargetSquare, n=1, include_self=False)

            for neighbor in targetNeighbors:
                neighborID = FUNC.getID(neighbor)
                #####same as original ID or also pushed for evading, dont change directions
                isTargetMine = FUNC.getIsTargetMine(PARAMS, neighborID)
                if isTargetMine == True:
                    if neighborID == origSquareID or PARAMS.allMySquares[neighborID]['pushedForEvading'] == True:
                        doing = None
                    else:
                        neighborTargetSquare = GLOBALVARS.game_map.get_target(neighbor, PARAMS.allMySquares[neighborID]['direction'])
                        neighborTargetSquareID = FUNC.getID(neighborTargetSquare)

                        if neighborTargetSquareID == origTargetID:
                            #####same target
                            if totalStrength + neighbor.strength > 255:
                                #####change direction of neighbor to still
                                PARAMS.allMySquares[neighborID]['direction'] = STILL
                            else:
                                #####increase total strength for next neighbor
                                totalStrength = totalStrength + neighbor.strength


################################################################################
#####
################################################################################
def manageOverStrengthDirection(PARAMS,GLOBALVARS):
    sortedList = reversed(sorted(PARAMS.allMySquaresList, key=lambda x: x.strength))

    for sq in sortedList:
        origID = FUNC.getID(sq)
        mySquaresDict = PARAMS.allMySquares[origID]
        origSquare = copy.copy(mySquaresDict['currentsquare'])
        origTargetID = copy.copy(mySquaresDict['actual_TowardID'])
        isTargetNeutral = FUNC.getIsTargetNeutral(PARAMS, origTargetID)
        isTargetMine = FUNC.getIsTargetMine(PARAMS, origTargetID)

        #####target square is yours
        #####target ID not managed yet
        #####target ID not orig ID
        if origTargetID not in PARAMS.managedTargetIDs and isTargetMine == True and origTargetID != origID:
            PARAMS.managedTargetIDs.append(origTargetID)
            totalStrength = 0
            origTargetSquare = copy.copy(PARAMS.allMySquares[origTargetID]["currentsquare"])
            targetTargetID = copy.copy(PARAMS.allMySquares[origTargetID]['actual_TowardID'])

            #####see if orig target targets itself
            if targetTargetID == origTargetID:
                totalStrength = copy.copy(PARAMS.allMySquares[origTargetID]['currentsquare'].strength)

            neighborsLowToHigh = FUNC.getNeighborsLowToHighStrength(GLOBALVARS,origTargetSquare)
            neighborsLowToHigh0 = copy.copy(neighborsLowToHigh)

            #####If there is a 255, make everyone going there still so this square can swap
            for neighbor in reversed(neighborsLowToHigh0):
                neighborID = FUNC.getID(neighbor)
                if FUNC.getIsTargetMine(PARAMS, neighborID):
                    neighborTargetID = copy.copy(PARAMS.allMySquares[neighborID]['actual_TowardID'])

                    #####has the same target
                    if neighborTargetID == origTargetID and neighbor.strength == PARAMS.maxStrength:
                        #####if there is a max strength, this is to prevent the rest from going there so max strength can swap
                        totalStrength = PARAMS.maxStrength

            #####first will be the lowest strength because you want to combine as much as possible
            for neighbor in reversed(neighborsLowToHigh):
                neighborID = FUNC.getID(neighbor)

                if FUNC.getIsTargetMine(PARAMS, neighborID):
                    neighborTargetID = copy.copy(PARAMS.allMySquares[neighborID]['actual_TowardID'])
                    #####has the same target

                    if neighborTargetID == origTargetID:
                        neighborTargetStrength = copy.copy(PARAMS.allMySquares[neighborID]['currentsquare'].strength)
                        if (totalStrength + neighborTargetStrength) > PARAMS.maxStrength:
                            #####keep neighbor at still, make orig square not to move here
                            PARAMS.allMySquares[neighborID]['direction'] = STILL
                            PARAMS.allMySquares[neighborID]['possibleSwap'] = True
                            PARAMS.allMySquares[neighborID]['temp_selftarget'] = True
                            PARAMS.allMySquares[neighborID]['actual_TowardID'] = copy.copy(neighborID)
                        else:
                            #####both neighbor and orig square can go to the target
                            totalStrength = totalStrength + neighborTargetStrength
                            #####to prevent swapping in the future
                            PARAMS.managedDontSwapAnymoreID.append(origTargetID)

        #####target square is a Neutral
        #####target ID not managed yet
        #####target ID not orig ID
        elif origTargetID not in PARAMS.managedTargetIDs and isTargetNeutral == True and origTargetID != origID:
            PARAMS.managedTargetIDs.append(origTargetID)
            totalStrength = 0
            origTargetSquare = copy.copy(PARAMS.allNeutralSquares[origTargetID]['currentsquare'])
            neutralStrength = copy.copy(PARAMS.allNeutralSquares[origTargetID]['currentsquare'].strength)
            totalStrength = totalStrength - neutralStrength
            #####get lowest neighbor first to attack neutral
            neighborsLowToHigh = FUNC.getNeighborsLowToHighStrength(GLOBALVARS,origTargetSquare)
            neighborsLowToHigh0 = copy.copy(neighborsLowToHigh)

            #####first will be highest, you want highest to go to direction-1 and attack
            for neighbor in reversed(neighborsLowToHigh0):
                neighborID = FUNC.getID(neighbor)
                #####origID already taken into account

                if FUNC.getIsTargetMine(PARAMS, neighborID):
                    neighborTargetID = copy.copy(PARAMS.allMySquares[neighborID]['actual_TowardID'])
                    if neighborTargetID == origTargetID:
                        neighborTargetStrength = copy.copy(PARAMS.allMySquares[neighborID]['currentsquare'].strength)
                        #####will be overstrength
                        #####neutral strength already subtracted from total strength
                        if (totalStrength + neighborTargetStrength) > PARAMS.maxStrength:
                            PARAMS.allMySquares[neighborID]['direction'] = STILL
                            PARAMS.allMySquares[neighborID]['possibleSwap'] = True
                            PARAMS.allMySquares[neighborID]['temp_selftarget'] = True
                            PARAMS.allMySquares[neighborID]['actual_TowardID'] = copy.copy(neighborID)
                        else:
                            totalStrength = totalStrength + neighborTargetStrength

        else:
            doing = None

################################################################################
#####This works with manageOverStrengthDirection
#####manages recursively the one that was changed to still
################################################################################
def manageOverStrengthDirectionSelfTargets(PARAMS):
    newOneJustSet = False
    sortedList = reversed(sorted(PARAMS.allMySquaresList, key=lambda x: x.strength))

    for sq in sortedList:
        origID = FUNC.getID(sq)
        mySquaresDict = PARAMS.allMySquares[origID]

        if mySquaresDict['temp_selftarget'] == True:
            mySquaresDict['temp_selftarget'] = False
            origSquare = mySquaresDict['currentsquare']
            totalStrength = copy.copy(mySquaresDict['currentsquare'].strength)
            neighbors = mySquaresDict['neighbors']

            #####find all that have the same target
            for directionKey, neighborDict in neighbors.items():
                neighborID = FUNC.getID(neighborDict['square'])

                if FUNC.getIsTargetMine(PARAMS, neighborID):
                    #####if neighbor's target is origID
                    if PARAMS.allMySquares[neighborID]['temp_selftarget'] == False and PARAMS.allMySquares[neighborID]['actual_TowardID'] == origID:
                        neighborTargetStrength = PARAMS.allMySquares[neighborID]['currentsquare'].strength
                        targetID = PARAMS.allMySquares[neighborID]['actual_TowardID']

                        if (totalStrength + neighborTargetStrength) <= PARAMS.maxStrength:
                            #####not going over, leave it alone
                            totalStrength = totalStrength + neighborTargetStrength
                            #####to prevent swapping in the future
                            PARAMS.managedDontSwapAnymoreID.append(targetID)
                        else:
                            #####Going over, change neighbors direction to STILL
                            PARAMS.allMySquares[neighborID]['direction'] = STILL
                            PARAMS.allMySquares[neighborID]['possibleSwap'] = True
                            PARAMS.allMySquares[neighborID]['temp_selftarget'] = True

                            PARAMS.allMySquares[neighborID]['actual_TowardID'] = copy.copy(neighborID)
                            newOneJustSet = True

    #####if new one was set above, need to run again
    if newOneJustSet == True:
        manageOverStrengthDirectionSelfTargets(PARAMS)

##############################################################################
#####
################################################################################
def manageOverStrengthDirectionSwapPosition(PARAMS,GLOBALVARS):
    sortedList =  reversed(sorted(PARAMS.allMySquaresList, key=lambda x: x.strength))

    for sq in sortedList:
        origID = FUNC.getID(sq)
        mySquaresDict = PARAMS.allMySquares[origID]
        origSquare = mySquaresDict['currentsquare']
        origDesiredTargetID = mySquaresDict['desired_TowardID']

        if FUNC.getIsTargetMine(PARAMS, origDesiredTargetID):
            desiredTargetSquare = PARAMS.allMySquares[origDesiredTargetID]["currentsquare"]
            #####not yet swapped
            #####only swap full strength

            #####removing check of if its max strength
            if mySquaresDict['possibleSwap'] == True \
                    and origID not in PARAMS.managedDontSwapAnymoreID \
                    and origDesiredTargetID not in PARAMS.managedDontSwapAnymoreID:

                if desiredTargetSquare.strength < origSquare.strength:
                    #####sometimes production doesnt show up in strength even though strength is that
                    if (desiredTargetSquare.strength + desiredTargetSquare.production) + (origSquare.strength + origSquare.production) > 255:
                        #####swap position
                        #####add id to swappedSquaresID list
                        PARAMS.managedDontSwapAnymoreID.append(origID)
                        PARAMS.managedDontSwapAnymoreID.append(origDesiredTargetID)
                        PARAMS.allMySquares[origID]['direction'] = DIR.getDirection(GLOBALVARS,origSquare,desiredTargetSquare)
                        PARAMS.allMySquares[origDesiredTargetID]['direction'] = DIR.getDirection(GLOBALVARS,desiredTargetSquare,origSquare)
                    else:
                        #####combine
                        PARAMS.managedDontSwapAnymoreID.append(origID)
                        PARAMS.managedDontSwapAnymoreID.append(origDesiredTargetID)
                        PARAMS.allMySquares[origID]['direction'] = DIR.getDirection(GLOBALVARS,origSquare, desiredTargetSquare)
                        PARAMS.allMySquares[origDesiredTargetID]['direction'] = STILL

################################################################################
#####Swap 2 with 1, if 1 is STILL and 2 is stronger than 1
################################################################################
def swap2with1(PARAMS,GLOBALVARS):
    for origID, mySquaresDict in PARAMS.allMySquares.items():

        if mySquaresDict['enemy_Distance'] == 2:
            nextSquare = mySquaresDict['enemy_NextSquare']
            nextSquareID = FUNC.getID(nextSquare)
            nextSquareIsOurs = FUNC.getIsTargetMine(PARAMS, nextSquareID)

            if nextSquareIsOurs \
                    and PARAMS.allMySquares[nextSquareID]['pushedForEvading'] == False \
                    and nextSquareID not in PARAMS.managedDontSwapAnymoreID \
                    and PARAMS.allMySquares[nextSquareID]['accountedForEvading'] == False \
                    and PARAMS.allMySquares[origID]['currentsquare'].strength > 100 \
                    and PARAMS.allMySquares[nextSquareID]['currentsquare'].strength < PARAMS.minSquareStrengthBeforeMoving  \
                    and PARAMS.allMySquares[nextSquareID]['attackPower'] - PARAMS.allMySquares[nextSquareID]['currentsquare'].strength + PARAMS.allMySquares[origID]['currentsquare'].strength < PARAMS.maxStrength:

                #####swap 2 with 1
                PARAMS.managedDontSwapAnymoreID.append(origID)
                PARAMS.managedDontSwapAnymoreID.append(nextSquareID)
                PARAMS.allMySquares[origID]['direction'] = DIR.getDirection(GLOBALVARS, mySquaresDict['currentsquare'],nextSquare)
                PARAMS.allMySquares[nextSquareID]['direction'] = DIR.getDirection(GLOBALVARS, nextSquare,mySquaresDict['currentsquare'])



