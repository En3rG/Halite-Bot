from collections import namedtuple, OrderedDict
import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import logging
import copy
import MyBotData as D
import MyBotFunctions as FUNC
import MyBotExpand as EXP
import MyBotDirections as DIR

################################################################################
#####
################################################################################
def initialize(GLOBALVARS,myID):
    #####To use best line or not
    GLOBALVARS.initExpand = True

    getSquaresInfo(GLOBALVARS,myID)
    setClosestEnemySquare(GLOBALVARS)
    #filteredList = getNeutralAreaRatio(GLOBALVARS)
    #bestTargets = getBestTargets(GLOBALVARS,filteredList)

    GLOBALVARS.bestLineOfAttackList = getBestLine(GLOBALVARS)
    getAreaRatioAroundStarting(GLOBALVARS, GLOBALVARS.starting_MySquare)
    setDirections(GLOBALVARS)

################################################################################
#####
################################################################################
def getSquaresInfo(GLOBALVARS,myID):
    for square in GLOBALVARS.game_map:
        id = FUNC.getID(square)
        #####Getting info of all squares
        neutralSquare = D.StartingNeutralTemplate()
        GLOBALVARS.starting_AllSquares[id] = neutralSquare.dict
        GLOBALVARS.starting_AllSquares[id]['currentsquare'] = square
        try:
            GLOBALVARS.starting_AllSquares[id]['ratio'] = square.production / square.strength
        except:
            #####strength = 0
            GLOBALVARS.starting_AllSquares[id]['ratio'] = square.production / 1.0
        GLOBALVARS.starting_AllSquares[id]['areaRatio'] = getAreaRatio(GLOBALVARS, square, myID)

        if square.owner == 0:
            neutralSquare = D.StartingNeutralTemplate()
            GLOBALVARS.starting_NeutralSquares[id] = neutralSquare.dict
            GLOBALVARS.starting_NeutralSquares[id]['currentsquare'] = square
            GLOBALVARS.starting_NeutralSquares[id]['ratio'] = copy.copy(GLOBALVARS.starting_AllSquares[id]['ratio'])
            GLOBALVARS.starting_NeutralSquares[id]['areaRatio'] = copy.copy(GLOBALVARS.starting_AllSquares[id]['areaRatio'])
        elif square.owner == myID:
            GLOBALVARS.starting_MySquare = square
        else:
            GLOBALVARS.starting_EnemySquares[id] = square

################################################################################
#####
################################################################################
def getAreaRatio(GLOBALVARS, currentsquare,myID):
    nextNeighbors = GLOBALVARS.game_map.neighbors(currentsquare, n=GLOBALVARS.neutralRatioArea,include_self=True)
    numSquares = 0
    totalRatio = 0
    for neighbor in nextNeighbors:
        if neighbor.owner == 0 or neighbor.owner != myID:
            numSquares = numSquares + 1
            try:
                # newRatio = ((neighbor.production) / neighbor.strength) + (neighbor.production/250)
                newRatio = ((neighbor.production) / neighbor.strength)
            except:
                #####if strength = 0
                newRatio = (neighbor.production) / 1
            totalRatio = totalRatio + newRatio

    areaRatio = totalRatio / numSquares

    return areaRatio

################################################################################
#####
################################################################################
def getAreaRatioAroundStarting(GLOBALVARS, currentsquare):
    nextNeighbors = GLOBALVARS.game_map.neighbors(currentsquare, n=5,include_self=True)
    numSquares = 0
    totalRatio = 0
    for neighbor in nextNeighbors:
        numSquares = numSquares + 1
        try:
            # newRatio = ((neighbor.production) / neighbor.strength) + (neighbor.production/250)
            newRatio = ((neighbor.production) / neighbor.strength)
        except:
            #####if strength = 0
            newRatio = (neighbor.production) / 1
        totalRatio = totalRatio + newRatio

    areaRatio = totalRatio / numSquares

    return areaRatio

################################################################################
#####
################################################################################
def setClosestEnemySquare(GLOBALVARS):
    Enemies = namedtuple('Enemies', 'currentsquare distance')
    enemyList = []

    for key, enemySquare in GLOBALVARS.starting_EnemySquares.items():
        distance = GLOBALVARS.game_map.get_distance(GLOBALVARS.starting_MySquare,enemySquare)
        newEnemy = Enemies(enemySquare,distance)
        enemyList.append(newEnemy)

    sortedList = sorted(enemyList, key=lambda x: x.distance)

    #####first item is the lowest distance
    GLOBALVARS.closestEnemySquare = sortedList[0].currentsquare

################################################################################
#####
################################################################################
def getNeutralAreaRatio(GLOBALVARS):
    Neutrals = namedtuple('Neutrals', 'currentsquare ratio areaRatio distanceFromStart')
    neutralList = []
    closestEnemyDistance = (GLOBALVARS.game_map.get_distance(GLOBALVARS.closestEnemySquare,GLOBALVARS.starting_MySquare))

    for keyID, neutralDict in GLOBALVARS.starting_NeutralSquares.items():
        currentSquare = neutralDict['currentsquare']

        areaRatio = GLOBALVARS.starting_NeutralSquares[keyID]['areaRatio']
        distanceFromStart = GLOBALVARS.game_map.get_distance(currentSquare, GLOBALVARS.starting_MySquare)
        newNeutral = Neutrals(currentSquare, neutralDict['ratio'], areaRatio, distanceFromStart)
        neutralList.append(newNeutral)

    ######sorts high to low
    sortedList = reversed(sorted(neutralList, key=lambda x: (x.areaRatio,x.distanceFromStart)))
    ######filter list within a certain distance
    maxDistance = 1.5*closestEnemyDistance
    filteredList = [namedTuple for namedTuple in sortedList if namedTuple.distanceFromStart < maxDistance]

    return filteredList

################################################################################
#####
################################################################################
def getBestTargets(GLOBALVARS,filteredList):
    numEnemies = len(GLOBALVARS.starting_EnemySquares)
    numPlayers = numEnemies + 1
    num = 0
    newList = []
    for item in filteredList:
        newList.append(item)
        num = num + 1
        if num == (numPlayers*2):
            break

    closestBest = sorted(newList, key=lambda x: x.distanceFromStart)

    return closestBest

###############################################################################
#####
################################################################################
def getBestLine(GLOBALVARS):
    startingSquare = GLOBALVARS.starting_MySquare
    mainSquareList = getLineList(GLOBALVARS,startingSquare)
    bestRatio = 0
    bestList = None
    length = copy.copy(GLOBALVARS.numOfSquaresInLineINIT)

    for currentList in mainSquareList:
        #####some may be shorter since it hit a square it already took into account before
        if len(set(currentList)) == length:
            currentTotal = 0
            currentListRatio = 0
            for square in currentList:
                try:
                    newRatio = square.production / square.strength
                except:
                    #####If strength = 0
                    newRatio = square.production

                currentTotal = currentTotal + newRatio

            currentListRatio = currentTotal/length

            if currentListRatio > bestRatio:
                bestRatio = copy.copy(currentListRatio)
                bestList = copy.copy(currentList)

    return bestList

################################################################################
#####
################################################################################
def getLineList(GLOBALVARS, currentsquare):
    mainSquareList = []
    currentSquareList = [currentsquare]
    generateList(GLOBALVARS, currentsquare, 2, mainSquareList, currentSquareList)

    return mainSquareList

################################################################################
#####
################################################################################
def generateList(GLOBALVARS, currentsquare, n, mainSquareList, currentList):
    numOfSquares = GLOBALVARS.numOfSquaresInLineINIT
    if n <= numOfSquares:
        for direction in (NORTH, EAST, SOUTH, WEST):
            nextSquare = GLOBALVARS.game_map.get_target(currentsquare, direction)

            if nextSquare in currentList:
                #####already exist in the list
                doing = None
            else:

                newList = copy.copy(currentList)
                newList.append(nextSquare)
                newNum = n + 1

                if newNum > numOfSquares:
                    mainSquareList.append(newList)
                else:
                    generateList(GLOBALVARS, nextSquare, newNum, mainSquareList, newList)

        return

################################################################################
#####
################################################################################
def setDirections(GLOBALVARS):
    allSquaresList = copy.copy(GLOBALVARS.bestLineOfAttackList)
    itemNum = 0
    for squares in allSquaresList:
        squaresID = FUNC.getID(squares)
        try:
            nextSquare = allSquaresList[itemNum+1]
        except:
            nextSquare = None
        GLOBALVARS.directions[squaresID] = nextSquare
        itemNum = itemNum + 1

################################################################################
#####
################################################################################
def expand(PARAMS,GLOBALVARS):
    totalNumSquaresAccounted = 0
    setDistanceForExpandingTargetLine(PARAMS, GLOBALVARS, totalNumSquaresAccounted)

    #####towards the line style
    # setDirectionsForExpandingTargetLine(PARAMS, GLOBALVARS)
    # updateDirectionOfOthersTowardsLineOnly(PARAMS, GLOBALVARS)

    #####towards the line but also expanding style
    EXP.setDistanceForExpandingTarget(PARAMS, GLOBALVARS, totalNumSquaresAccounted)
    setDirectionsForExpandingTargetLine(PARAMS, GLOBALVARS)
    reachedLastSquareInLine(PARAMS, GLOBALVARS)

################################################################################
#####set all directions for params
################################################################################
def setDirectionsForExpandingTargetLine(PARAMS,GLOBALVARS):
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

                            else:
                                directionMovement = DIR.getDirection(GLOBALVARS, square, targetSquare)
                                PARAMS.allMySquares[ID]['direction'] = directionMovement

                                #####check if it has enemy next to target
                                hasEnemy, enemyList, numOfenemies = FUNC.hasEnemyNeighbor(PARAMS, GLOBALVARS, targetSquare)
                                if hasEnemy:
                                    GLOBALVARS.hasEnemyBeenDetected = True
                                    PARAMS.allMySquares[ID]['direction'] = STILL


################################################################################
#####
################################################################################
def setDistanceForExpandingTargetLine(PARAMS,GLOBALVARS,totalNumSquaresAccounted):
    #####Iterate through neutrals, highest priority first, until all our squares are accounted for
    squaresList = copy.copy(GLOBALVARS.bestLineOfAttackList)
    for square in squaresList:
        if totalNumSquaresAccounted < len(PARAMS.allMySquares):
            id = FUNC.getID(square)
            if FUNC.getIsTargetNeutral(PARAMS,id):
                neutralList = [square]
                mainTarget = neutralList[0]
                distanceNum = 1
                numOfSquares = 0
                totalNumSquaresAccounted = totalNumSquaresAccounted + EXP.setExpandingTarget(PARAMS, GLOBALVARS, mainTarget,neutralList, distanceNum, numOfSquares)

################################################################################
#####
################################################################################
def updateDirectionOfOthersTowardsLineOnly(PARAMS,GLOBALVARS):
    for keyID, mySquaresDict in PARAMS.allMySquares.items():
        if mySquaresDict['expanding_Distance'] == 0 and mySquaresDict['currentsquare'].strength > GLOBALVARS.minSquareStrengthBeforeMovingMiddleINITLine:

            if FUNC.checkIfIDExistInDictionary(PARAMS, GLOBALVARS, keyID, GLOBALVARS.directions):
                if GLOBALVARS.directions[keyID] == None:
                    GLOBALVARS.initExpand = False
                else:
                    # PARAMS.allMySquares[keyID]['direction'] = DIR.getDirection(GLOBALVARS,mySquaresDict['currentsquare'], GLOBALVARS.directions[keyID])

                    #####Get direction of our closest square towards the final target
                    square = mySquaresDict['currentsquare']
                    sortedSquaresList = reversed(copy.copy(GLOBALVARS.bestLineOfAttackList))
                    for neighbor in sortedSquaresList:
                        neighborID = FUNC.getID(neighbor)
                        if FUNC.getIsTargetMine(PARAMS, neighborID) and FUNC.getIsTargetANeighbor(PARAMS, GLOBALVARS,square, neighborID):
                            PARAMS.allMySquares[keyID]['direction'] = DIR.getDirection(GLOBALVARS, square, neighbor)

                            #####check if it has enemy next to target
                            hasEnemy, enemyList, numOfenemies = FUNC.hasEnemyNeighbor(PARAMS, GLOBALVARS, neighbor)
                            if hasEnemy:
                                GLOBALVARS.hasEnemyBeenDetected = True
                                PARAMS.allMySquares[keyID]['direction'] = STILL
                            break

################################################################################
#####
################################################################################
def reachedLastSquareInLine(PARAMS,GLOBALVARS):
    for keyID, mySquaresDict in PARAMS.allMySquares.items():
        if mySquaresDict['expanding_Distance'] == 0:
            if FUNC.checkIfIDExistInDictionary(PARAMS, GLOBALVARS, keyID, GLOBALVARS.directions):
                if GLOBALVARS.directions[keyID] == None:
                    GLOBALVARS.initExpand = False


