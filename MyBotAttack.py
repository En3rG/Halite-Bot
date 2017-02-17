import copy
import MyBotDirections as DIR
import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import logging
import MyBotFunctions as FUNC

################################################################################
#####
################################################################################
def setDistanceFromFakeEnemy(PARAMS, GLOBALVARS, neutralFrontLine, distanceNum):
    _distanceNum = copy.copy(distanceNum)
    _neutralFrontLine = copy.copy(neutralFrontLine)

    for sq in _neutralFrontLine:
        ####No enemy square
        targetSquare = copy.copy(sq)
        newNeutralFrontLine = []
        nextNeighbors = GLOBALVARS.game_map.neighbors(sq, n=1, include_self=False)

        for neighbor in nextNeighbors:
            if neighbor.owner == PARAMS.myID:
                id = FUNC.getID(neighbor)
                if (PARAMS.allMySquares[id]["enemy_Distance"] == 0 and (PARAMS.allMySquares[id]["fakeEnemy_Distance"] == 0) \
                        or PARAMS.allMySquares[id]["fakeEnemy_Distance"] > _distanceNum):
                    PARAMS.allMySquares[id]["fakeEnemy_Distance"] = _distanceNum
                    PARAMS.allMySquares[id]["fakeEnemy_NextSquare"] = copy.copy(sq)
                    PARAMS.allMySquares[id]["fakeEnemy_TargetSquare"] = copy.copy(targetSquare)
                    newNeutralFrontLine.append(neighbor)

                    if id not in PARAMS.accountedIDsToAttack:
                        PARAMS.accountedIDsToAttack.append(id)

                    if id not in PARAMS.deletedFromExpandingSquaresID:
                        PARAMS.deletedFromExpandingSquaresID.append(id)

        if _distanceNum == copy.copy(PARAMS.poweringBackUpNum):
            #####reached max distance allowed
            return
        else:
            #####get next distance
            setDistanceFromFakeEnemy(PARAMS,GLOBALVARS, newNeutralFrontLine, _distanceNum + 1)

################################################################################
#####
################################################################################
def setDistanceFromEnemy(PARAMS, GLOBALVARS, neutralFrontLine, distanceNum):
    _distanceNum = copy.copy(distanceNum)
    _neutralFrontLine = copy.copy(neutralFrontLine)

    for sq in _neutralFrontLine:
        ####get enemy square
        nextNeighbors1 = GLOBALVARS.game_map.neighbors(sq, n=1, include_self=False)
        enemySquare = None

        for _neighbor in nextNeighbors1:
            if _neighbor.owner != PARAMS.myID and _neighbor.owner != 0:
                enemySquare = copy.copy(_neighbor)
                break

        newNeutralFrontLine = []
        nextNeighbors2 = GLOBALVARS.game_map.neighbors(sq, n=1, include_self=False)

        for neighbor in nextNeighbors2:
            if neighbor.owner == PARAMS.myID:
                id = FUNC.getID(neighbor)
                if PARAMS.allMySquares[id]["enemy_Distance"] == 0 or PARAMS.allMySquares[id]["enemy_Distance"] > _distanceNum:
                    #####lower enemy distance found
                    PARAMS.allMySquares[id]["enemy_Distance"] = _distanceNum
                    PARAMS.allMySquares[id]["enemy_NextSquare"] = sq
                    PARAMS.allMySquares[id]["enemy_TargetSquare"] = copy.copy(enemySquare)
                    newNeutralFrontLine.append(neighbor)

                    if id not in PARAMS.accountedIDsToAttack:
                        PARAMS.accountedIDsToAttack.append(copy.copy(id))

                    if id not in PARAMS.deletedFromExpandingSquaresID:
                        PARAMS.deletedFromExpandingSquaresID.append(copy.copy(id))

            elif neighbor.owner == 0 and neighbor.strength == 0:
                newNeutralFrontLine.append(neighbor)
            else:
                doing = None

        if _distanceNum == copy.copy(PARAMS.callForBackupNum):
            return
        else:
            setDistanceFromEnemy(PARAMS,GLOBALVARS, newNeutralFrontLine, _distanceNum + 1)

################################################################################
#####set all directions for params
################################################################################
def setDirectionsInParamsAttacking(PARAMS, GLOBALVARS):
    for keyID, mySquaresDict in PARAMS.allMySquares.items():
        if GLOBALVARS.OLDPARAMS is not None:
            setPreviousDistanceFromEnemy(PARAMS, GLOBALVARS, keyID, mySquaresDict)
            setPreviousnextSquarePerEnemy(PARAMS, GLOBALVARS, keyID, mySquaresDict)
        if PARAMS.allMySquares[keyID]['accountedForEvading'] == True:
            #####is evading, already has direction.
            doing = None
        elif PARAMS.allMySquares[keyID]['enemy_Distance'] > 0 or PARAMS.allMySquares[keyID]['enemy_Distance-1'] > 0:
            setDirectionsInParams(PARAMS, GLOBALVARS, keyID, mySquaresDict)
        elif PARAMS.allMySquares[keyID]['fakeEnemy_Distance'] > 0:
            setDirectionsInParamsFake(PARAMS, GLOBALVARS, keyID, mySquaresDict)
        else:
            doing = None

################################################################################
#####
################################################################################
def setPreviousDistanceFromEnemy(PARAMS, GLOBALVARS, key,mySquaresDict):
    square = mySquaresDict['currentsquare']
    id = FUNC.getID(square)
    try:
        PARAMS.allMySquares[id]['enemy_Distance-1'] = GLOBALVARS.OLDPARAMS.allMySquares[id]['enemy_Distance']
    except:
        #####That id didnt exist in oldparams
        PARAMS.allMySquares[id]['enemy_Distance-1'] = 0

################################################################################
#####
################################################################################
def setPreviousnextSquarePerEnemy(PARAMS, GLOBALVARS, key, mySquaresDict):
    square = mySquaresDict['currentsquare']
    id = FUNC.getID(square)

    try:
        PARAMS.allMySquares[id]['enemy_NextSquare-1'] = GLOBALVARS.OLDPARAMS.allMySquares[id]['enemy_NextSquare']
    except:
        #####That id didnt exist in oldparams
        PARAMS.allMySquares[id]['enemy_NextSquare-1'] = ""

################################################################################
#####set all directions for params
################################################################################
def setDirectionsInParams(PARAMS,GLOBALVARS, key,mySquaresDict):
    currentProduction = mySquaresDict['currentsquare'].production
    minSquareStrengthBeforeMovingTime = PARAMS.turnsToStayBeforeMoving * currentProduction
    square = mySquaresDict['currentsquare']
    id = FUNC.getID(square)
    hasNeutral0, neutral0 = FUNC.hasNeutralNeighborWithStrength0(PARAMS, GLOBALVARS, square)

    if hasNeutral0 and mySquaresDict['enemy_Distance'] != 1 and mySquaresDict['enemy_Distance'] != 2 and square.strength > 0:
        directionMovement = DIR.getDirection(GLOBALVARS, square, neutral0)
    elif mySquaresDict['currentsquare'].strength < PARAMS.minSquareStrengthBeforeMoving:
        directionMovement = STILL
    elif (mySquaresDict['enemy_Distance'] == 2):
        #####prevent splash damage
        if mySquaresDict['currentsquare'].strength > PARAMS.strengthToForceMove_2:
            #####go to 1 position
            directionMovement = DIR.getDirection(GLOBALVARS,square, mySquaresDict['enemy_NextSquare'])
        else:
            directionMovement = STILL
    elif (mySquaresDict['enemy_Distance'] == 4):
        #####prevent splash damage
        if mySquaresDict['currentsquare'].strength > PARAMS.strengthToForceMove_4:
            #####go to 3 position
            directionMovement = DIR.getDirection(GLOBALVARS,square, mySquaresDict['enemy_NextSquare'])
        else:
            directionMovement = STILL
    elif (mySquaresDict['enemy_Distance'] == 0) and (mySquaresDict['enemy_Distance-1'] == 2):
        #####number 1 before won, move forward
        directionMovement = DIR.getDirection(GLOBALVARS,square, mySquaresDict['enemy_NextSquare-1'])
    elif (mySquaresDict['enemy_Distance'] == 1) and mySquaresDict['enemy_Distance-1'] == 2:
        #####number 1 before lost, move forward
        directionMovement = DIR.getDirection(GLOBALVARS,square, mySquaresDict['enemy_NextSquare'])
    elif (mySquaresDict['enemy_Distance'] == 1):
        #directionMovement = DIR.getDirectionFromPriority(mySquaresDict, PARAMS)
        directionMovement = DIR.getDirectionFromPriorityExcluding(mySquaresDict, PARAMS,[])
    elif mySquaresDict['enemy_Distance'] == PARAMS.createOpeningDistanceFromEnemy and square.strength > PARAMS.minStrengthCreateOpening:
        #####has to have neutrals around it
        hasNeutral, neutralSq = FUNC.hasNeutralNeighbor(PARAMS, GLOBALVARS, square)
        if hasNeutral == True:
            #directionMovement = DIR.getDirectionFromPriority(mySquaresDict, PARAMS)
            directionMovement = DIR.getDirection(GLOBALVARS,square, neutralSq)
        else:
            #####else go with direction of enemy distance
            id = FUNC.getID(square)
            directionMovement = getDirectionFromEnemyDistance(PARAMS, GLOBALVARS, id)
    else:
        directionMovement = getDirectionFromEnemyDistance(PARAMS, GLOBALVARS, id)

    PARAMS.allMySquares[key]['direction'] = directionMovement

################################################################################
#####
################################################################################
def getDirectionFromEnemyDistance(PARAMS, GLOBALVARS, id):
    currentsquare = PARAMS.allMySquares[id]['currentsquare']
    nextLocationsquare_0 = PARAMS.allMySquares[id]["enemy_NextSquare"]
    nextLocationsquare_1 = PARAMS.allMySquares[id]["enemy_NextSquare-1"]
    enemyDistance_0 = PARAMS.allMySquares[id]["enemy_Distance"]
    enemyDistance_1 = PARAMS.allMySquares[id]["enemy_Distance-1"]

    if enemyDistance_0 == 0 and enemyDistance_1 > 0:
        #####use old data
        return DIR.getDirection(GLOBALVARS,currentsquare, nextLocationsquare_1)
    elif enemyDistance_1 < enemyDistance_0 and enemyDistance_1 != 0:
        return DIR.getDirection(GLOBALVARS,currentsquare, nextLocationsquare_1)
    else:
        return DIR.getDirection(GLOBALVARS,currentsquare, nextLocationsquare_0)

################################################################################
#####set all directions for params
################################################################################
def getfakeNeutralfrontline(PARAMS):
    fakeNeutralfrontlineNamedTple = sorted(PARAMS.neutralSquaresDetectedEnemy, key=lambda x: x.priority)
    fakeNeutralfrontline = []

    for tple in fakeNeutralfrontlineNamedTple:
        fakeNeutralfrontline.append(tple.currentsquare)

    return fakeNeutralfrontline

################################################################################
#####set all directions for params
################################################################################
def setDirectionsInParamsFake(PARAMS,GLOBALVARS, key,mySquaresDict):
    currentProduction = mySquaresDict['currentsquare'].production
    minSquareStrengthBeforeMovingTime = PARAMS.turnsToStayBeforeMoving * currentProduction
    square = mySquaresDict['currentsquare']
    nextSquare = mySquaresDict["fakeEnemy_NextSquare"]
    id = FUNC.getID(square)
    hasNeutral0, neutral0 = FUNC.hasNeutralNeighborWithStrength0(PARAMS, GLOBALVARS, square)

    if hasNeutral0 and square.strength > 0:
        directionMovement = DIR.getDirection(GLOBALVARS, square, neutral0)
    elif mySquaresDict['fakeEnemy_Distance'] == 1 and mySquaresDict['currentsquare'].strength < PARAMS.minSquareStrengthPoweringUp_1:
        #####check if next to neutral neighbor
        directionMovement = STILL
    elif mySquaresDict['fakeEnemy_Distance'] > 1 and mySquaresDict['currentsquare'].strength < PARAMS.minSquareStrengthPoweringUp:
        directionMovement = STILL
    elif mySquaresDict['currentsquare'].strength <= nextSquare.strength and nextSquare.owner == 0:
        #####Not strong enough to take the neutral
        directionMovement = STILL
    else:
        #####Next square is neutral
        if PARAMS.preventAttackingFirst == True:
            if square.strength > PARAMS.minStrengthToAttackNeutralEnemyDetected:
                directionMovement = DIR.getDirection(GLOBALVARS, square, nextSquare)
            else:
                #####get best priority excluding ones towards the enemy
                excludeList = []
                for direction in (NORTH, EAST, SOUTH, WEST):
                    newNextSquare = GLOBALVARS.game_map.get_target(square, direction)
                    hasEnemy, enemyList, numOfenemies = FUNC.hasEnemyNeighbor(PARAMS, GLOBALVARS, newNextSquare)
                    if hasEnemy == True:
                        excludeList.append(direction)

                if excludeList == []:
                    #directionMovement = DIR.getDirectionFromPriorityExcluding(mySquaresDict, PARAMS, excludeList)
                    directionMovement = DIR.getDirection(GLOBALVARS, square, nextSquare)
                    targetSquare = GLOBALVARS.game_map.get_target(square, directionMovement)
                    targetSquareID = FUNC.getID(targetSquare)

                    if GLOBALVARS.OLDPARAMS is not None:
                        if FUNC.checkIfIDExistInDictionary(PARAMS, GLOBALVARS, id,GLOBALVARS.OLDPARAMS.mySquaresAlongEnemyBorder) \
                                and targetSquareID == GLOBALVARS.OLDPARAMS.mySquaresAlongEnemyBorder[id]:
                            excludeList.append(directionMovement)
                            directionMovement = (max(excludeList) + 1) % 4
                        else:
                            directionMovement = DIR.getDirection(GLOBALVARS, square, nextSquare)

                else:
                    #####since NORTH == 0, will not be the max
                    if WEST in excludeList and NORTH in excludeList and EAST not in excludeList:
                        directionMovement = EAST
                    elif WEST in excludeList and NORTH in excludeList and EAST in excludeList:
                        directionMovement = SOUTH
                    else:
                        directionMovement = (max(excludeList) + 1) % 4
                    targetSquare = GLOBALVARS.game_map.get_target(square, directionMovement)
                    targetSquareID = FUNC.getID(targetSquare)
                    PARAMS.mySquaresAlongEnemyBorder[targetSquareID] = copy.copy(id)

                    if GLOBALVARS.OLDPARAMS is not None:
                        if FUNC.checkIfIDExistInDictionary(PARAMS, GLOBALVARS, id, GLOBALVARS.OLDPARAMS.mySquaresAlongEnemyBorder) \
                            and targetSquareID == GLOBALVARS.OLDPARAMS.mySquaresAlongEnemyBorder[id]:
                            excludeList.append(directionMovement)
                            directionMovement = (max(excludeList) + 1) % 4

                #####Make sure square is strong enough to take if its a neutral
                newTargetSquare = GLOBALVARS.game_map.get_target(square, directionMovement)
                if mySquaresDict[
                    'currentsquare'].strength <= newTargetSquare.strength and newTargetSquare.owner == 0:
                    #####Not strong enough to take the neutral
                    directionMovement = STILL

        else:
            #####Not preventing first attack, just get best priority excluding help priority
            excludeList = []
            directionMovement = DIR.getDirectionFromPriorityExcluding(mySquaresDict, PARAMS,excludeList)

            targetSquare = GLOBALVARS.game_map.get_target(square, directionMovement)
            if targetSquare.owner == PARAMS.myID:
                #####just take the neutral square next to enemy, instead of going back and forth
                directionMovement = DIR.getDirection(GLOBALVARS, square, nextSquare)

    PARAMS.allMySquares[key]['direction'] = directionMovement

