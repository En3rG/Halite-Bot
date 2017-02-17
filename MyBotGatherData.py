import MyBotData as D
from collections import namedtuple, OrderedDict
import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import copy
import MyBotFunctions as FUNC

################################################################################
#####
################################################################################
def getSquaresInfo(PARAMS,GLOBALVARS):
    #####get all your squares data including:
    #####neighbors, neighbors priority, and neutrals in front line
    for square in GLOBALVARS.game_map:
        id = FUNC.getID(square)

        if square.owner == PARAMS.myID:
            PARAMS.allMySquaresList.append(square)
            mySquares = D.MySquaresTemplate()
            PARAMS.allMySquares[id] = mySquares.dict
            PARAMS.allMySquares[id]['currentsquare'] = square
            PARAMS.allMySquares[id]['neighbors'] = getNeutralSquaresInTheBorderWithPriority(PARAMS, GLOBALVARS,square)

        elif square.owner == 0:
            PARAMS.allNeutralSquaresList.append(square)
            neutralSquare = D.NeutralTemplate()
            PARAMS.allNeutralSquares[id] = neutralSquare.dict
            PARAMS.allNeutralSquares[id]['currentsquare'] = square
            try:
                PARAMS.allNeutralSquares[id]['ratio'] = square.production / square.strength
            except:
                #####if strength = 0
                PARAMS.allNeutralSquares[id]['ratio'] = square.production / 1.0

        else:
            #####Enemy Squares
            doing = None

################################################################################
#####Returns next neighbors with priority (for neutrals and enemy)
################################################################################
def getNeutralSquaresInTheBorderWithPriority(PARAMS, GLOBALVARS, current_square,):
    nextNeighbors = GLOBALVARS.game_map.neighbors(current_square, n=1, include_self=False)
    tempNeighborDict = {}
    priority = 0
    for neighbor in nextNeighbors:
        if GLOBALVARS.turn < PARAMS.openingGameTurns:
            priority = getPriorityForNeighborsDictLine(PARAMS, GLOBALVARS, neighbor)
        else:
            priority = getPriorityForNeighborsDictArea(PARAMS, GLOBALVARS, neighbor)
        tempNeighbordict = {}
        tempNeighbordict['square'] = neighbor
        tempNeighbordict['neighborPriority'] = priority

        if current_square.x == neighbor.x:
            if current_square.y < neighbor.y:
                if neighbor.y - current_square.y == 1:
                    tempNeighborDict['south'] = tempNeighbordict
                else:
                    #####loop around
                    tempNeighborDict['north'] = tempNeighbordict
            else:
                if current_square.y - neighbor.y == 1:
                    tempNeighborDict['north'] = tempNeighbordict
                else:
                    #####loop around
                    tempNeighborDict['south'] = tempNeighbordict
        else:
            #####current_square.y == neighbor.y
            if current_square.x < neighbor.x:
                if neighbor.x - current_square.x == 1:
                    tempNeighborDict['east'] = tempNeighbordict
                else:
                    #####loop around
                    tempNeighborDict['west'] = tempNeighbordict
            else:
                if current_square.x - neighbor.x == 1:
                    tempNeighborDict['west'] = tempNeighbordict
                else:
                    #####loop around
                    tempNeighborDict['east'] = tempNeighbordict

        if neighbor.owner == 0:
            #####Add to neutral squares in border with priority
            NeutralSquare = namedtuple('NeutralSquare', 'currentsquare priority')
            newSquare = NeutralSquare(neighbor,priority)
            PARAMS.neutralSquaresInTheBorderWithPriority.append(newSquare)

    return tempNeighborDict

################################################################################
#####Returns priority level for neutral squares and with enemies
################################################################################
def getPriorityForNeighborsDictArea(PARAMS, GLOBALVARS, neighbor):
    if neighbor.owner == 0:
        if neighbor.strength == 0:
            #####neutral with no strength, check its neighbors
            nextNeighbors = GLOBALVARS.game_map.neighbors(neighbor, n=1, include_self=False)
            enemies = 0
            neutrals = 0
            allies = 0
            for sq in nextNeighbors:
                if sq.owner == 0:
                    neutrals = neutrals + 1
                elif sq.owner == PARAMS.myID:
                    allies = allies + 1
                else:
                    neighborID = FUNC.getID(neighbor)
                    #####its an enemy square, this neutral is in the front line
                    PARAMS.neutralSquaresInFrontLine.append(neighbor)
                    PARAMS.neutralSquaresInFrontLineIDs.append(neighborID)
                    GLOBALVARS.hasEnemyBeenEngaged = True
                    enemies = enemies + 1

            if enemies == 3:
                return (40 + getAreaRatio(PARAMS,GLOBALVARS, neighbor))
            elif enemies == 2:
                return (30 + getAreaRatio(PARAMS,GLOBALVARS, neighbor))
            elif enemies == 1:
                return (20 + getAreaRatio(PARAMS,GLOBALVARS, neighbor))
            else:
                if neighbor.production > 0:
                    return (10 + getAreaRatio(PARAMS,GLOBALVARS, neighbor))
                else:
                    return -0.75

        else:
            priority = getAreaRatio(PARAMS, GLOBALVARS, neighbor)
            # priority = getBestLineRatio(params, neighbor)
            if priority == 0:
                return -0.75
            else:
                return float(priority)

    else:
        #####Can only be our square
        return -1.00

################################################################################
#####Return area ratio (including enemies and neutrals) of a given area
#####Your units not included
################################################################################
def getAreaRatio(PARAMS,GLOBALVARS,currentsquare):
    if GLOBALVARS.useINITAreaRatio == True:
        #####New way, just get from initialized value
        currentsquareID = FUNC.getID(currentsquare)
        return GLOBALVARS.starting_AllSquares[currentsquareID]['areaRatio']
    else:
        #####Old way, calculated per turn
        nextNeighbors = GLOBALVARS.game_map.neighbors(currentsquare, n=PARAMS.neutralRatioArea, include_self=True)
        numSquares = 0
        totalRatio = 0
        for neighbor in nextNeighbors:
            if neighbor.owner == 0 or neighbor.owner != PARAMS.myID:
                numSquares = numSquares + 1
                try:
                    #newRatio = ((neighbor.production) / neighbor.strength) + (neighbor.production/250)
                    newRatio = ((neighbor.production) / neighbor.strength)
                except:
                    #####if strength = 0
                    newRatio = (neighbor.production)/1
                totalRatio = totalRatio + newRatio

        areaRatio = totalRatio / numSquares

        return areaRatio

################################################################################
#####Returns priority level for neutral squares and with enemies
################################################################################
def getPriorityForNeighborsDictLine(PARAMS,GLOBALVARS,  neighbor):
    if neighbor.owner == PARAMS.myID:
        return -1
    else:
        #####Neutral or Enemy squares
        return getBestLineRatio(PARAMS, GLOBALVARS,neighbor)

###############################################################################
#####
################################################################################
def getBestLineRatio(PARAMS, GLOBALVARS, currentsquare):
    mainSquareList = getLineRatio(PARAMS, GLOBALVARS,currentsquare)
    bestRatio = 0
    currentTotal = 0
    for currentList in mainSquareList:
        length = len(currentList)
        n = 1
        for square in currentList:
            try:
                #newRatio = ((square.production)/square.strength) + (square.production/250)
                newRatio = ((square.production) / square.strength)
            except:
                newRatio = ((square.production)/1)

            if square.owner != PARAMS.myID and square.owner != 0:
                GLOBALVARS.hasEnemyBeenEngaged = True
                newRatio = newRatio + 40

            currentTotal = currentTotal + newRatio
            n = n + 1
        currentRatio = currentTotal/length

        if currentRatio > bestRatio:
            bestRatio = copy.copy(currentRatio)

    return bestRatio

################################################################################
#####
################################################################################
def getLineRatio(PARAMS,GLOBALVARS, currentsquare):
    mainSquareList = []
    currentSquareList = [currentsquare]
    getLineRatioList(PARAMS,GLOBALVARS, currentsquare, 2, mainSquareList, currentSquareList)

    return mainSquareList

################################################################################
#####
################################################################################
def getLineRatioList(PARAMS,GLOBALVARS, currentsquare, n, mainSquareList, currentList):
    if n <= PARAMS.neutralRatioLine:
        for direction in (NORTH, EAST, SOUTH, WEST):
            nextSquare = GLOBALVARS.game_map.get_target(currentsquare, direction)

            if nextSquare.owner != PARAMS.myID:
                newList = copy.copy(currentList)
                newList.append(nextSquare)
                newNum = n + 1

                if newNum > PARAMS.neutralRatioLine:
                    mainSquareList.append(newList)
                else:
                    getLineRatioList(PARAMS,GLOBALVARS, nextSquare, newNum, mainSquareList, newList)

        return

################################################################################
#####
################################################################################
def getNeutralSquaresDetectedEnemy(PARAMS, GLOBALVARS):
    for namedtple in PARAMS.neutralSquaresInTheBorderWithPriority:
        neutralBorder = namedtple.currentsquare
        nextNeighbors = GLOBALVARS.game_map.neighbors(neutralBorder, n=PARAMS.distanceFromEnemyStartPoweringUp, include_self=False)
        for sq in nextNeighbors:
            if sq.owner != 0 and sq.owner != PARAMS.myID:
                PARAMS.neutralSquaresDetectedEnemy.append(namedtple)
                break

