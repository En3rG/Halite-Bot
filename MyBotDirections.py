import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import copy
import random
import logging
import MyBotFunctions as FUNC
from collections import namedtuple, OrderedDict

################################################################################
#####set all directions, return moves
################################################################################
def setDirections(PARAMS, moves):
    for squareID, mySquaresDict in PARAMS.allMySquares.items():
        sq = mySquaresDict['currentsquare']
        direction = mySquaresDict['direction']
        moves.append(Move(sq, direction))

    #####For 1 line
    # return [Move(mySquaresDict['currentsquare'], mySquaresDict['direction']) for squareID, mySquaresDict in PARAMS.allMySquares.items()]

    return moves

################################################################################
#####return a direction
#####take direction that overlaps the map into account
################################################################################
def getDirection(GLOBALVARS,current_square, current_neighbor):
    distance = GLOBALVARS.game_map.get_distance(current_square, current_neighbor)
    #####same y
    if current_neighbor.x > current_square.x and current_neighbor.y == current_square.y:
        if distance < (current_neighbor.x - current_square.x):
            return WEST
        else:
            return EAST
    #####same y
    elif current_neighbor.x < current_square.x and current_neighbor.y == current_square.y:
        if distance < (current_square.x - current_neighbor.x):
            return EAST
        else:
            return WEST
    #####same x
    elif current_neighbor.x == current_square.x and current_neighbor.y < current_square.y:
        if distance < (current_square.y - current_neighbor.y):
            return SOUTH
        else:
            return NORTH
    #####same x
    elif current_neighbor.x == current_square.x and current_neighbor.y > current_square.y:
        if distance < (current_neighbor.y - current_square.y):
            return NORTH
        else:
            return SOUTH
    #####to the left/down, diagonally
    elif current_neighbor.x < current_square.x and current_neighbor.y > current_square.y:
        if distance < ((current_square.x - current_neighbor.x) + (current_neighbor.y - current_square.y)):
            return random.choice((EAST,SOUTH))
        else:
            return random.choice((WEST, SOUTH))
    #####to the right/down, diagonally
    elif current_neighbor.x > current_square.x and current_neighbor.y > current_square.y:
        if distance < ((current_neighbor.x - current_square.x) + (current_neighbor.y - current_square.y)):
            return random.choice((WEST, SOUTH))
        else:
            return random.choice((EAST, SOUTH))
    #####to the right/up, diagonally
    elif current_neighbor.x > current_square.x and current_neighbor.y < current_square.y:
        if distance < ((current_neighbor.x - current_square.x) + (current_square.y - current_neighbor.y)):
            return random.choice((WEST, NORTH))
        else:
            return random.choice((EAST, NORTH))
    #####to the left/up, diagonally
    else:
        if distance < ((current_square.x - current_neighbor.x) + (current_square.y - current_neighbor.y)):
            return random.choice((EAST, NORTH))
        else:
            return random.choice((WEST, NORTH))

################################################################################
#####
################################################################################
def getDirectionFromPriority(square_dict,PARAMS):

    priority = -10.000
    direction_id = None

    for direction, neighborsDict in square_dict["neighbors"].items():
        #####loop through the neighbors of the current square
        if neighborsDict["neighborPriority"] == -1:
            #####if neighbor priority is -1, its an ally
            #####check its request help priority (which should be its highest neighbor priority)
            neighborSquare = neighborsDict["square"]
            id = FUNC.getID(neighborSquare)
            realneighborSquare = copy.copy(PARAMS.allMySquares[id])
            if realneighborSquare["requestHelpPriority"] > priority:
                priority = copy.copy(PARAMS.allMySquares[id]["requestHelpPriority"])
                direction_id = copy.copy(direction)
        elif neighborsDict["neighborPriority"] > priority:
            priority = copy.copy(neighborsDict["neighborPriority"])
            direction_id = copy.copy(direction)
        else:
            doing = None

    if direction_id == "north":
        _direction = NORTH
    elif direction_id == "east":
        _direction = EAST
    elif direction_id == "south":
        _direction = SOUTH
    else:
        _direction = WEST

    #####If highest priority is a neutral, check if it has stronger strength
    neighborSquare = square_dict["neighbors"][direction_id]["square"]
    currentsquare = copy.copy(square_dict["currentsquare"])

    if neighborSquare.owner == 0:
        if currentsquare.strength <= neighborSquare.strength and neighborSquare.strength != 255:
            _direction = STILL

    return _direction

################################################################################
#####Excluding help priority and given exclude direction
################################################################################
def getDirectionFromPriorityExcluding(square_dict,PARAMS,excludeDirection):
    highestPriority = -10.000
    bestDirectionID = None
    _direction = STILL

    for direction in (NORTH,EAST,SOUTH,WEST):
        if direction in excludeDirection:
            #####dont take into account
            doing = None
        else:
            if direction == NORTH:
                directionID = 'north'
            elif direction == EAST:
                directionID = 'east'
            elif direction == SOUTH:
                directionID = 'south'
            else:
                directionID = 'west'

            neighborPriority = square_dict["neighbors"][directionID]["neighborPriority"]

            #####If -1, no need to check help request priority, this causes back and forth
            if neighborPriority > highestPriority:
                highestPriority = copy.copy(neighborPriority)
                bestDirectionID = directionID
                _direction = direction
            else:
                doing = None

    #####If highest priority is a neutral, check if it has stronger strength
    neighborSquare = square_dict["neighbors"][bestDirectionID]["square"]
    currentsquare = copy.copy(square_dict["currentsquare"])

    if neighborSquare.owner == 0:
        if currentsquare.strength <= neighborSquare.strength and neighborSquare.strength != 255:
            _direction = STILL

    return _direction

################################################################################
#####Manage squares in the middle
#####Get closests neutral (frontline) then change its direction
################################################################################
def updateDirectionOfMiddleSquares(PARAMS,GLOBALVARS):
    for keyID, mySquaresDict in PARAMS.allMySquares.items():
        if mySquaresDict['expanding_Distance'] == 0 \
                and mySquaresDict['enemy_Distance'] == 0 \
                and mySquaresDict['enemy_Distance-1'] == 0 \
                and mySquaresDict['fakeEnemy_Distance'] == 0 \
                and mySquaresDict['currentsquare'].strength > PARAMS.minSquareStrengthBeforeMoving \
                and mySquaresDict['currentsquare'].strength > PARAMS.turnsToStayBeforeMoving*mySquaresDict['currentsquare'].production:

            currentsquare = mySquaresDict['currentsquare']

            #####if lower than 32x32
            if GLOBALVARS.maxturns < 321:
                #####this one gets closest neutral in frontline if it exist, if not get closest neutral
                #####maybe taking too much time though (but this is way better)
                direction = getDirectionClosestNeutralFrontline(PARAMS,GLOBALVARS,currentsquare)
                PARAMS.allMySquares[keyID]['direction'] = checkIFEnoughToTakeOverNeutral(GLOBALVARS, currentsquare, direction)

            else:
                #direction = getDirectionNotOurSquare(PARAMS, GLOBALVARS, currentsquare)
                #####new version, goes to enemy if it exists
                direction = getDirectionNotOurSquare2(PARAMS, GLOBALVARS, currentsquare)
                #direction = getDirectionNotOurSquare3(PARAMS, GLOBALVARS, currentsquare)
                PARAMS.allMySquares[keyID]['direction'] = checkIFEnoughToTakeOverNeutral(GLOBALVARS, currentsquare, direction)

################################################################################
#####
################################################################################
def getDirectionClosestNeutralFrontline(PARAMS, GLOBALVARS,currentsquare):
    distance = 10000
    closestNeutralFrontlineSquare = None

    for sq in PARAMS.neutralSquaresInFrontLine:
        newdistance = GLOBALVARS.game_map.get_distance(currentsquare, sq)

        if newdistance < distance:
            distance = newdistance
            closestNeutralFrontlineSquare = sq

    if closestNeutralFrontlineSquare is not None and distance < PARAMS.maxDistanceFromMiddleToEnemy:
        #####get closest neutral in frontline if any exist
        #####and its close enough
        newdirection = getDirection(GLOBALVARS,currentsquare, closestNeutralFrontlineSquare)
    else:
        #####no frontline neutral exist, go for any neutral
        newdirection, distance = getDirectionClosestNeutral(PARAMS,GLOBALVARS,currentsquare)

        #####if distance is below max distance from middle stay time, stay/still
        #####otherwise use direction from closest Neutral
        if distance < PARAMS.maxDistanceFromMiddleToStayTime:
            currentProduction = currentsquare.production
            minSquareStrengthBeforeMovingTime = PARAMS.turnsToStayBeforeMoving * currentProduction

            if currentsquare.strength < minSquareStrengthBeforeMovingTime:
                newdirection = STILL

    return newdirection

################################################################################
#####
################################################################################
def getDirectionClosestNeutral(PARAMS,GLOBALVARS,currentsquare):
    distance = 10000
    closestNeutralSquare = None

    for neutralSquare in PARAMS.neutralSquaresInTheBorderWithPriority:
        sq = copy.copy(neutralSquare.currentsquare)
        newdistance = GLOBALVARS.game_map.get_distance(currentsquare, sq)

        if newdistance < distance:
            distance = newdistance
            closestNeutralSquare = sq

    newdirection = getDirection(GLOBALVARS,currentsquare, closestNeutralSquare)

    return newdirection, distance

################################################################################
#####
################################################################################
def getDirectionNotOurSquare(PARAMS, GLOBALVARS, currentsquare):
    finalDirection = random.choice((NORTH,EAST))
    closestDistance = min(GLOBALVARS.game_map.width, GLOBALVARS.game_map.height) / 2
    for direction in (NORTH, EAST, SOUTH, WEST):
        distance = 0
        current = currentsquare
        while current.owner == PARAMS.myID and distance < closestDistance:
            distance = distance + 1
            current = GLOBALVARS.game_map.get_target(current, direction)

        if distance < closestDistance:
            finalDirection = direction
            closestDistance = distance
    return finalDirection

################################################################################
#####
################################################################################
def getDirectionNotOurSquare2(PARAMS, GLOBALVARS, currentsquare):
    closestNeutralDistance = min(GLOBALVARS.game_map.width, GLOBALVARS.game_map.height) / 2
    closestEnemyDistance = min(GLOBALVARS.game_map.width, GLOBALVARS.game_map.height) / 2
    directionToEnemy = None
    directionToNeutral = None

    for direction in (NORTH, EAST, SOUTH, WEST):
        distanceToNeutral = 0
        distanceToEnemy = 0
        currentSquareForNeutral = copy.copy(currentsquare)
        currentSquareForEnemy = copy.copy(currentsquare)

        #####Will never reach enemy since it'll be neutral with 0 first
        while (currentSquareForNeutral.owner == PARAMS.myID and distanceToNeutral < closestNeutralDistance) or \
                ((currentSquareForEnemy.owner == PARAMS.myID or (currentSquareForEnemy.owner ==  0 and currentSquareForEnemy.strength == 0)) and distanceToEnemy < closestEnemyDistance):
            if currentSquareForNeutral.owner == PARAMS.myID and distanceToNeutral < closestNeutralDistance:
                distanceToNeutral = distanceToNeutral + 1
                currentSquareForNeutral = GLOBALVARS.game_map.get_target(currentSquareForNeutral, direction)
            if (currentSquareForEnemy.owner == PARAMS.myID or (currentSquareForEnemy.owner ==  0 and currentSquareForEnemy.strength == 0)) and distanceToEnemy < closestEnemyDistance:
                distanceToEnemy = distanceToEnemy + 1
                currentSquareForEnemy = GLOBALVARS.game_map.get_target(currentSquareForEnemy, direction)

        if currentSquareForNeutral.owner == 0 and distanceToNeutral < closestNeutralDistance:
            #####Found neutral
            directionToNeutral = direction
            closestNeutralDistance = distanceToNeutral

        if currentSquareForEnemy.owner != 0 and currentSquareForEnemy.owner != PARAMS.myID and distanceToEnemy < closestEnemyDistance:
            #####Found Enemy
            directionToEnemy = direction
            closestEnemyDistance = distanceToEnemy

    if directionToEnemy is not None:
        finalDirection = directionToEnemy
    elif directionToNeutral is not None:
        finalDirection = directionToNeutral
    else:
        finalDirection = random.choice((NORTH, EAST))

    return finalDirection

################################################################################
#####
################################################################################
def getDirectionNotOurSquare3(PARAMS, GLOBALVARS, currentsquare):
    closestNeutralDistance = min(GLOBALVARS.game_map.width, GLOBALVARS.game_map.height) / 2
    closestEnemyDistance = min(GLOBALVARS.game_map.width, GLOBALVARS.game_map.height) / 2
    directionToEnemy = None
    directionToNeutral = None
    neutralList = []
    NeutralSquare = namedtuple('NeutralSquare', 'currentsquare areaRatio direction')

    for direction in (NORTH, EAST, SOUTH, WEST):
        distanceToNeutral = 0
        distanceToEnemy = 0
        currentSquareForNeutral = copy.copy(currentsquare)
        currentSquareForEnemy = copy.copy(currentsquare)

        #####Will never reach enemy since it'll be neutral with 0 first
        while (currentSquareForNeutral.owner == PARAMS.myID and distanceToNeutral < closestNeutralDistance) or \
                ((currentSquareForEnemy.owner == PARAMS.myID or (currentSquareForEnemy.owner ==  0 and currentSquareForEnemy.strength == 0)) and distanceToEnemy < closestEnemyDistance):
            if currentSquareForNeutral.owner == PARAMS.myID and distanceToNeutral < closestNeutralDistance:
                distanceToNeutral = distanceToNeutral + 1
                currentSquareForNeutral = GLOBALVARS.game_map.get_target(currentSquareForNeutral, direction)
            if (currentSquareForEnemy.owner == PARAMS.myID or (currentSquareForEnemy.owner ==  0 and currentSquareForEnemy.strength == 0)) and distanceToEnemy < closestEnemyDistance:
                distanceToEnemy = distanceToEnemy + 1
                currentSquareForEnemy = GLOBALVARS.game_map.get_target(currentSquareForEnemy, direction)

        if currentSquareForNeutral.owner == 0:
            #####Found neutral
            currentSquareForNeutralID = FUNC.getID(currentSquareForNeutral)
            areaRatio = GLOBALVARS.starting_AllSquares[currentSquareForNeutralID]['areaRatio']
            newSquare = NeutralSquare(currentSquareForNeutral, areaRatio, direction)
            neutralList.append(newSquare)

        if currentSquareForEnemy.owner != 0 and currentSquareForEnemy.owner != PARAMS.myID and distanceToEnemy < closestEnemyDistance:
            #####Found Enemy
            directionToEnemy = direction
            closestEnemyDistance = distanceToEnemy

    if directionToEnemy is not None:
        finalDirection = directionToEnemy
    elif neutralList != []:
        highTolow = reversed(sorted(neutralList, key=lambda x: x.areaRatio))

        for item in highTolow:
            finalDirection = item.direction
            break
    else:
        finalDirection = random.choice((NORTH, EAST))

    return finalDirection

################################################################################
#####
################################################################################
def getDirectionNotOurSquareExclude(PARAMS, GLOBALVARS, currentsquare, excludeList):
    finalDirection = random.choice((NORTH,EAST))
    closestDistance = min(GLOBALVARS.game_map.width, GLOBALVARS.game_map.height) / 2
    for direction in (NORTH, EAST, SOUTH, WEST):
        if direction in excludeList:
            doing = None
        else:
            distance = 0
            current = currentsquare
            while current.owner == PARAMS.myID and distance < closestDistance:
                distance = distance + 1
                current = GLOBALVARS.game_map.get_target(current, direction)

            if distance < closestDistance:
                finalDirection = direction
                closestDistance = distance
    return finalDirection

################################################################################
#####
################################################################################
def checkIFEnoughToTakeOverNeutral(GLOBALVARS,square, directionMovement):
    targetSquare = GLOBALVARS.game_map.get_target(square,directionMovement)

    if targetSquare.owner == 0:
        if square.strength > targetSquare.strength:
            return directionMovement
        else:
            #####Not strong enough to take neutral
            return STILL
    else:
        #####Not neutral
        return directionMovement

