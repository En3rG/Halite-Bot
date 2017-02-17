import copy
import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import MyBotDirections as DIR
import logging
from collections import namedtuple, OrderedDict
import MyBotAttack as ATK
import MyBotExpand as EXP
import MyBotEvade as EV

################################################################################
#####
################################################################################
def attackAndExpand(PARAMS,GLOBALVARS):
    #####Work together (expanding and attacking)-----------------
    #####---Gather Attacking squares
    distanceNum = 1

    neutralfrontline = PARAMS.neutralSquaresInFrontLine
    ATK.setDistanceFromEnemy(PARAMS, GLOBALVARS, neutralfrontline, distanceNum)

    fakeNeutralfrontline = ATK.getfakeNeutralfrontline(PARAMS)
    ATK.setDistanceFromFakeEnemy(PARAMS, GLOBALVARS, fakeNeutralfrontline, distanceNum)

    totalNumSquaresAccounted = len(PARAMS.accountedIDsToAttack)
    ATK.setDirectionsInParamsAttacking(PARAMS, GLOBALVARS)

    ####---Gather Expanding squares
    totalNumSquaresAccounted = EXP.getOldNeutralTarget(PARAMS, GLOBALVARS)
    EXP.setDistanceForExpandingTarget(PARAMS, GLOBALVARS, totalNumSquaresAccounted)
    EXP.setDirectionsInParamsOpening(PARAMS, GLOBALVARS)

################################################################################
#####
################################################################################
def setTarget(PARAMS,GLOBALVARS):
    for keyID, mySquaresDict in PARAMS.allMySquares.items():
        square = copy.copy(mySquaresDict['currentsquare'])
        direction = copy.copy(mySquaresDict['direction'])
        targetID = getTargetID(GLOBALVARS,square,direction)
        PARAMS.allMySquares[keyID]['desired_TowardID'] = copy.copy(targetID)
        PARAMS.allMySquares[keyID]['actual_TowardID'] = copy.copy(targetID)

################################################################################
#####
################################################################################
def getTargetID(GLOBALVARS,square,direction):
    targetSquare = GLOBALVARS.game_map.get_target(square,direction)
    return getID(targetSquare)

################################################################################
#####
################################################################################
def getID(square):
    return str(square.x) + "_" + str(square.y)

################################################################################
#####Returns a list of neighbors, from low to high (base on strength)
################################################################################
def getNeighborsLowToHighStrength(GLOBALVARS,square):
    #####get neighbors
    nextNeighbors = GLOBALVARS.game_map.neighbors(square, n=1, include_self=False)
    return sorted(nextNeighbors, key=lambda x: x.strength)

################################################################################
#####
################################################################################
def getIsTargetMine(PARAMS, targetID):
    try:
        test = PARAMS.allMySquares[targetID]
        found = True
    except:
        found = False
    return found

################################################################################
#####
################################################################################
def getIsTargetNeutral(PARAMS, targetID):
    try:
        test = PARAMS.allNeutralSquares[targetID]['currentsquare']
        neutral = True
    except:
        neutral = False
    return neutral

################################################################################
#####
################################################################################
def getIsTargetANeighbor(PARAMS,GLOBALVARS, square, neighborID):
    #####assumes target is our square
    neighbors = GLOBALVARS.game_map.neighbors(square, n=1, include_self=False)
    neighborsList = []
    for neighbor in neighbors:
        _neighborID = getID(neighbor)
        neighborsList.append(_neighborID)
    if neighborID in neighborsList:
        return True
    else:
        return False

################################################################################
#####
################################################################################
def getIsOneOfListANeighbor(PARAMS, GLOBALVARS, square, listIDs):
    #####assumes target is our square
    neighbors = GLOBALVARS.game_map.neighbors(square, n=1, include_self=False)
    neighborsList = []
    for neighbor in neighbors:
        _neighborID = getID(neighbor)
        neighborsList.append(_neighborID)
    for ID in listIDs:
        if ID in neighborsList:
            return True

    #####No match
    return False

################################################################################
#####set help priority base on highest neighbor's priority
################################################################################
def setRequestHelpPriority(PARAMS,GLOBALVARS):
    OurSquare = namedtuple('OurSquare', 'currentsquare requestpriority neighborsList')
    ourSquareList = []
    ####Set all requestHelpPriority
    for key, mySquaresDict in PARAMS.allMySquares.items():
        currentSq = mySquaresDict['currentsquare']
        neighbors = mySquaresDict['neighbors']
        highestPriority = -1000.00
        neighborsList = []
        for direction, neighborsDict in neighbors.items():
            neighborsList.append(neighborsDict["square"])
            if neighborsDict["neighborPriority"] > highestPriority:
                highestPriority = neighborsDict["neighborPriority"]

        priority = (PARAMS.requestHelpPriorityPercent) * (highestPriority)
        PARAMS.allMySquares[key]["requestHelpPriority"] = priority
        newSquare = OurSquare(currentSq, priority,neighborsList)
        ourSquareList.append(newSquare)

    #####Go through from highest to lowest, updating if found a higher one
    sortedList = reversed(sorted(ourSquareList, key=lambda x: x.requestpriority))
    for nmdtple in sortedList:
        currentsquare = nmdtple.currentsquare
        currentID = getID(currentsquare)
        currentRequestPriority = nmdtple.requestpriority
        for neighbor in nmdtple.neighborsList:
            neighborID = getID(neighbor)

            if neighbor.owner == PARAMS.myID:
                newpriority = PARAMS.allMySquares[neighborID]["requestHelpPriority"] * PARAMS.requestHelpPriorityPercent
                if newpriority > currentRequestPriority:
                    currentRequestPriority = copy.copy(newpriority)

        PARAMS.allMySquares[currentID]["requestHelpPriority"] = currentRequestPriority

################################################################################
#####
################################################################################
def hasNeutralNeighborWithStrength0(PARAMS, GLOBALVARS, square):
    neighbors = GLOBALVARS.game_map.neighbors(square, n=1, include_self=False)
    hasNeutral = False
    neutral0 = None
    for neighbor in neighbors:
        if neighbor.owner == 0 and neighbor.strength == 0:
            hasNeutral = True
            neutral0 = neighbor
            break

    return hasNeutral, neutral0

################################################################################
#####
################################################################################
def hasNeutralNeighbor(PARAMS, GLOBALVARS, square):
    neighbors = GLOBALVARS.game_map.neighbors(square, n=1, include_self=False)
    hasNeutral = False
    neutralSquare = None

    for neighbor in neighbors:
        if neighbor.owner == 0:
            hasNeutral = True
            neutralSquare = neighbor
            break

    return hasNeutral, neutralSquare

################################################################################
#####set help priority base on highest neighbor's priority
################################################################################
def hasEnemyNeighbor(PARAMS, GLOBALVARS, square):
    neighbors = GLOBALVARS.game_map.neighbors(square, n=1, include_self=False)
    hasEnemy = False
    enemyList = []
    numOfEnemies = 0
    for neighbor in neighbors:
        if neighbor.owner != 0 and neighbor.owner != PARAMS.myID:
            hasEnemy = True
            enemyList.append(neighbor)
            numOfEnemies = numOfEnemies + 1

    return hasEnemy, enemyList, numOfEnemies

################################################################################
#####
################################################################################
def checkIfIDExistInDictionary(PARAMS, GLOBALVARS, ID, givenDictionary):
    try:
        test = givenDictionary[ID]
        #####exist already
        return True
    except:
        return False