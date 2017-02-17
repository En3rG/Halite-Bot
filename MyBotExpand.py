import logging
import copy
import MyBotData as D
import MyBotDirections as DIR
import MyBotFunctions as FUNC

################################################################################
#####
################################################################################
def getOldNeutralTarget(PARAMS, GLOBALVARS):
    totalNumOldSquaresAccounted = 0
    addPreviousEnemyDistancesToDeletedExpandingSquares(PARAMS, GLOBALVARS)

    if GLOBALVARS.OLDPARAMS is not None:
        for mainTargetID, dictionary in GLOBALVARS.OLDPARAMS.neutralExpandingTargets.items():
            mainTarget = dictionary['currentsquare']
            takeOldData, numOldSquaresAccounted = copyPreviousNeutralTargets(PARAMS,GLOBALVARS,mainTargetID,mainTarget)

            if takeOldData == True:
                totalNumOldSquaresAccounted = totalNumOldSquaresAccounted + numOldSquaresAccounted
        return totalNumOldSquaresAccounted
    else:
        return 0

################################################################################
#####
################################################################################
def addPreviousEnemyDistancesToDeletedExpandingSquares(PARAMS, GLOBALVARS):
    if GLOBALVARS.OLDPARAMS is not None:
        for keyID, mySquareDict in GLOBALVARS.OLDPARAMS.allMySquares.items():
            if mySquareDict['enemy_Distance'] == 0 and mySquareDict['enemy_Distance-1'] > 0:
                PARAMS.deletedFromExpandingSquaresID.append(keyID)

################################################################################
#####
################################################################################
def copyPreviousNeutralTargets(PARAMS, GLOBALVARS, mainTargetID, mainTarget):
    takeOldData = False
    numOldSquaresAccounted = 0
    #####see if it exist in previous data
    if FUNC.checkIfIDExistInDictionary(PARAMS, GLOBALVARS, mainTargetID, GLOBALVARS.OLDPARAMS.neutralExpandingTargets):
        oldDict = GLOBALVARS.OLDPARAMS.neutralExpandingTargets[mainTargetID]
        if oldDict['moveSquareWithDistance'] == 0 or oldDict['moveSquareWithDistance'] == 1:
            doing = None
        else:
            lostExpandingSquares = checkIfAnyExpandingSquaresTaken(PARAMS,GLOBALVARS,oldDict['expandingSquares'])

            if lostExpandingSquares == False:
                #####Copy previous data minus 1
                takeOldData = True
                newMoveSquareDistance = oldDict['moveSquareWithDistance'] - 1
                neutralTemplate = D.NeutralTargetTemplate(mainTargetID,mainTarget,newMoveSquareDistance)
                PARAMS.neutralExpandingTargets[mainTargetID] = neutralTemplate.dict

                #####Copy Old Attacking Squares minus the one that moved before
                for distanceID, listOfSquares in oldDict['expandingSquares'].items():
                    if int(distanceID) <= newMoveSquareDistance:
                        PARAMS.neutralExpandingTargets[mainTargetID]['expandingSquares'][distanceID] = []

                        for square in listOfSquares:
                            squareID = FUNC.getID(square)
                            PARAMS.neutralExpandingTargets[mainTargetID]['expandingSquares'][distanceID].append(square)
                            numOldSquaresAccounted = numOldSquaresAccounted + 1
                            PARAMS.allMySquares[squareID]["expanding_Distance"] = copy.copy(int(distanceID))
                            PARAMS.allMySquares[squareID]["expanding_NextSquare"] = copy.copy(GLOBALVARS.OLDPARAMS.allMySquares[squareID]["expanding_NextSquare"])
                            PARAMS.allMySquares[squareID]["expanding_TargetSquare"] = copy.copy(mainTarget)

    return takeOldData, numOldSquaresAccounted

################################################################################
#####
################################################################################
def checkIfAnyExpandingSquaresTaken(PARAMS,GLOBALVARS,attackingDict):
    takenSomewhereElse = False

    for distanceID, listOfSquares in attackingDict.items():
        for sq in listOfSquares:
            sqID = FUNC.getID(sq)
            if sqID in PARAMS.deletedFromExpandingSquaresID:
                takenSomewhereElse = True
                return takenSomewhereElse
    return takenSomewhereElse

################################################################################
#####
################################################################################
def setDistanceForExpandingTarget(PARAMS,GLOBALVARS,totalNumSquaresAccounted):
    #####Iterate through neutrals, highest priority first, until all our squares are accounted for
    sortedList = reversed(sorted(PARAMS.neutralSquaresInTheBorderWithPriority, key=lambda x: x.priority))
    for item in sortedList:
        if totalNumSquaresAccounted < len(PARAMS.allMySquares):
            neutralList = [item.currentsquare]
            mainTarget = neutralList[0]
            distanceNum = 1
            numOfSquares = 0
            totalNumSquaresAccounted = totalNumSquaresAccounted + setExpandingTarget(PARAMS, GLOBALVARS, mainTarget,neutralList, distanceNum, numOfSquares)

################################################################################
#####Get highest priority targets until accounted squares is >= number of squares owned
#####generate almost the same as backup for enemy, but for neutral target
################################################################################
def setExpandingTarget(PARAMS, GLOBALVARS, mainTarget, Target, distanceNum, numOfSquares):
    mainTargetID = FUNC.getID(mainTarget)
    if FUNC.checkIfIDExistInDictionary(PARAMS, GLOBALVARS, mainTargetID, PARAMS.neutralExpandingTargets):
        #####exist already
        return 0
    else:
        #####doesnt exist yet
        moveDistance = 0
        neutralTemplate = D.NeutralTargetTemplate(mainTargetID, mainTarget, moveDistance)
        PARAMS.neutralExpandingTargets[mainTargetID] = neutralTemplate.dict
        numSqueresAccounted = setDistanceFromNeutral(PARAMS, GLOBALVARS,mainTarget, mainTargetID, Target, distanceNum,numOfSquares)
        return numSqueresAccounted

################################################################################
#####
################################################################################
def setDistanceFromNeutral(PARAMS, GLOBALVARS, mainTarget, mainTargetID, Target, distanceNum, numOfSquares):
    currentDistance = copy.copy(distanceNum)
    _Target = copy.copy(Target)
    PARAMS.neutralExpandingTargets[mainTargetID]['expandingSquares'][currentDistance] = []
    isEnough = False
    almostEnough = False

    for sq in _Target:
        newTarget = []
        noneLeft = True
        nextNeighbors = GLOBALVARS.game_map.neighbors(sq, n=1, include_self=False)
        for neighbor in nextNeighbors:
            if neighbor.owner == PARAMS.myID:
                id = FUNC.getID(neighbor)
                if PARAMS.allMySquares[id]["expanding_Distance"] == 0 and PARAMS.allMySquares[id]['enemy_Distance'] == 0 and PARAMS.allMySquares[id]['fakeEnemy_Distance'] == 0:

                    if PARAMS.allMySquares[id]['currentsquare'].strength < PARAMS.forceMinStrengthForExpanding:
                        #####Dont take into account, skip
                        doing = None
                    else:
                        #####If distance is not 0, this square has been taken into account already
                        PARAMS.allMySquares[id]["expanding_Distance"] = currentDistance
                        PARAMS.allMySquares[id]["expanding_NextSquare"] = sq
                        PARAMS.allMySquares[id]["expanding_TargetSquare"] = mainTarget
                        newTarget.append(neighbor)
                        numOfSquares = numOfSquares + 1
                        noneLeft = False
                        PARAMS.neutralExpandingTargets[mainTargetID]['expandingSquares'][currentDistance].append(neighbor)
                        isEnough, almostEnough = checkIfAttackingUnitsAreEnough(PARAMS, GLOBALVARS, mainTarget, mainTargetID,numOfSquares, currentDistance)

                        if isEnough == True:
                            PARAMS.neutralExpandingTargets[mainTargetID]['moveSquareWithDistance'] = copy.copy(currentDistance)
                            break
                        elif almostEnough == True:
                            #####This ID (distance) wont have any attacking squares, but will be moved next turn
                            PARAMS.neutralExpandingTargets[mainTargetID]['moveSquareWithDistance'] = (currentDistance+1)
                            break
                        else:
                            doing = None

    if isEnough == False and noneLeft == False:
        numOfSquares = setDistanceFromNeutral(PARAMS,GLOBALVARS, mainTarget, mainTargetID, newTarget, currentDistance + 1,numOfSquares)

    return numOfSquares

################################################################################
#####
################################################################################
def checkIfAttackingUnitsAreEnough(PARAMS, GLOBALVARS, mainTarget, mainTargetID, numOfSquares, maxDistance):
    neutralStrength = mainTarget.strength
    totalStrength = 0
    extraStrengthOneMoreStay = 0
    isEnough = False
    almostEnough = False
    for key, squareList in PARAMS.neutralExpandingTargets[mainTargetID]['expandingSquares'].items():
        distance = int(key)
        for square in squareList:
            extraStrength = (maxDistance - distance) * square.production
            totalStrength = totalStrength + extraStrength + square.strength
            extraStrengthOneMoreStay = extraStrengthOneMoreStay + square.production

    if totalStrength > neutralStrength:
        isEnough = True
        almostEnough = True

    else:
        isEnough = False
        almostEnough = False

    return isEnough, almostEnough

################################################################################
#####set all directions for params
################################################################################
def setDirectionsInParamsOpening(PARAMS,GLOBALVARS):
    for targetID, dictionary in PARAMS.neutralExpandingTargets.items():
        if dictionary['moveSquareWithDistance'] == 0:
            doing = None
        else:
            moveSquareWithDistanceID = dictionary['moveSquareWithDistance']

            for distanceID, squareList in dictionary['expandingSquares'].items():
                if distanceID == moveSquareWithDistanceID:
                    for square in squareList:

                        ID = FUNC.getID(square)
                        if FUNC.getIsTargetMine(PARAMS, ID):
                            targetSquare = PARAMS.allMySquares[ID]['expanding_NextSquare']

                            if PARAMS.allMySquares[ID]['currentsquare'].strength == 0:
                                PARAMS.allMySquares[ID]['direction'] = STILL

                            elif PARAMS.allMySquares[ID]['enemy_Distance'] > 0 or PARAMS.allMySquares[ID]['enemy_Distance-1'] > 0:
                                #####Do not change its direction, handled by attack direction
                                doing = None
                            elif PARAMS.allMySquares[ID]['fakeEnemy_Distance'] > 0:
                                #####Do not change its direction, handled by attack direction
                                doing = None
                            else:
                                targetSquare = PARAMS.allMySquares[ID]['expanding_NextSquare']
                                directionMovement = DIR.getDirection(GLOBALVARS,square,targetSquare)
                                PARAMS.allMySquares[ID]['direction'] = directionMovement


