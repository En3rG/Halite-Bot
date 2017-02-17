import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import logging
import MyBotDirections as DIR
import copy
import MyBotFunctions as FUNC
import MyBotManage as MG
import itertools

################################################################################
#####
################################################################################
def evadeTowardsEnemy(PARAMS, GLOBALVARS):
    evadeTowardsWithEnemyDistance1(PARAMS,GLOBALVARS)
    getNeighborsOfNeutralBordersCloseToEnemy(PARAMS, GLOBALVARS)
    evadeDistance2ButNoDistance1(PARAMS, GLOBALVARS)
    MG.manageOverStrengthPushed(PARAMS, GLOBALVARS)

################################################################################
#####
################################################################################
def getBestCombo(PARAMS, GLOBALVARS, squaresList):
    bestComboStrength = 0
    bestsubset = None

    for currentLength in range(0, len(squaresList)+1):
        #####subset will be all combination of that currentLength
        for subset in itertools.permutations(squaresList, currentLength):
            currentcombo= 0
            #####add all strength in the given subset
            for square in subset:
                currentcombo = currentcombo + square.strength

            if currentcombo > bestComboStrength and currentcombo <= PARAMS.maxStrength:
                bestsubset = subset
                bestComboStrength = currentcombo

    return bestComboStrength,bestsubset


################################################################################
#####Manages squares around a neutral frontline
#####Then manages squares next to neutral with 0 strength next to the original neutral frontline
################################################################################
def evadeTowardsWithEnemyDistance1(PARAMS, GLOBALVARS):
    newListNoDuplicate = []
    newIDs = []
    #####Delete duplicates (if any)
    for neutralFrontLine in PARAMS.neutralSquaresInFrontLine:
        neutralFrontLineID = FUNC.getID(neutralFrontLine)
        if neutralFrontLineID not in newIDs:
            newIDs.append(neutralFrontLineID)
            newListNoDuplicate.append(neutralFrontLine)

    for neutralFrontLine in newListNoDuplicate:
        neutralFrontLineID = FUNC.getID(neutralFrontLine)

        #####GET NEIGHBORS GOING TO NEUTRAL FRONT LINE
        #####With enemy distance #1
        enemySquare, squaresHittingFrontlineList, nextNeighborNeutralsWith0, combineStrength, squaresWithDistance2, squareIsHandledBefore, squaresHandledBeforeList = getOurSquaresToFrontLine(PARAMS, GLOBALVARS, neutralFrontLine)


        if squareIsHandledBefore == True:
            attackingStrength = 0
            attackSquares = []
            pushSquares = []
            for square in squaresHandledBeforeList:
                attackingStrength = attackingStrength + square.strength

            for sq in squaresHittingFrontlineList:
                sqID = FUNC.getID(sq)
                PARAMS.allMySquares[sqID]["accountedForEvading"] = True

                if attackingStrength + sq.strength <= PARAMS.maxStrength:
                    attackSquares.append(sq)
                else:
                    pushSquares.append(sq)

            for attackSquare in attackSquares:
                if attackSquare.strength > 0:
                    attackSquareID = FUNC.getID(attackSquare)
                    PARAMS.allMySquares[attackSquareID]["direction"] = DIR.getDirection(GLOBALVARS,attackSquare,neutralFrontLine)
                    attackingStrength = attackingStrength + attackSquare.strength

            #####Set attack power
            for square in squaresHandledBeforeList:
                squareID = FUNC.getID(square)
                PARAMS.allMySquares[squareID]["attackPower"] = attackingStrength

            for attackSquare in attackSquares:
                attackSquareID = FUNC.getID(attackSquare)
                PARAMS.allMySquares[attackSquareID]["attackPower"] = attackingStrength

            directionTowardsEnemy = DIR.getDirection(GLOBALVARS, neutralFrontLine, enemySquare)
            for pushSquare in pushSquares:
                pushForwardOrPushBack(PARAMS, GLOBALVARS, pushSquare, neutralFrontLineID, directionTowardsEnemy)

        elif combineStrength > PARAMS.maxStrength and len(squaresHittingFrontlineList) > 1:
            #####NEED TO DO SOME KIND OF EVASION
            directionTowardsEnemy = DIR.getDirection(GLOBALVARS, neutralFrontLine, enemySquare)
            attackingStrength = 0

            if len(squaresHittingFrontlineList) == 2:
                #####At this point, we know the 2 squares cannot be combined
                #####Use towards enemy method, unless one will hit a neutral, then use push back method.
                highToLowList = []
                highToLow = reversed(sorted(squaresHittingFrontlineList, key=lambda x: x.strength))
                for item in highToLow:
                    itemID = FUNC.getID(item)
                    PARAMS.allMySquares[itemID]["accountedForEvading"] = True
                    highToLowList.append(item)

                attackSquare = highToLowList[0]
                pushSquare = highToLowList[1]
                attackSquareID = FUNC.getID(attackSquare)
                PARAMS.allMySquares[attackSquareID]["attackPower"] = attackSquare.strength
                PARAMS.allMySquares[attackSquareID]["direction"] = DIR.getDirection(GLOBALVARS, attackSquare,neutralFrontLine)
                attackingStrength = attackSquare.strength
                pushSquareID = FUNC.getID(pushSquare)

                if pushSquare.strength > 0:
                    pushForwardOrPushBack(PARAMS, GLOBALVARS, pushSquare, neutralFrontLineID, directionTowardsEnemy)

            else:
                #####len(squaresHittingFrontlineList) == 3
                #####2 squares may still be able to combine and be below 255 strength
                bestComboStrength, bestsubset = getBestCombo(PARAMS, GLOBALVARS, squaresHittingFrontlineList)
                attackSquares = []
                pushSquares = []
                for square in squaresHittingFrontlineList:
                    if square in bestsubset:
                        attackSquares.append(square)
                    else:
                        pushSquares.append(square)

                for attackSquare in attackSquares:
                    if attackSquare.strength > 0:
                        attackSquareID = FUNC.getID(attackSquare)
                        #logging.debug("attackSquare#: %s \n", attackSquare)
                        PARAMS.allMySquares[attackSquareID]["direction"] = DIR.getDirection(GLOBALVARS, attackSquare, neutralFrontLine)
                        attackingStrength = attackingStrength + attackSquare.strength

                #####Set attack power
                for attackSquare in attackSquares:
                    attackSquareID = FUNC.getID(attackSquare)
                    PARAMS.allMySquares[attackSquareID]["attackPower"] = attackingStrength

                for pushSquare in pushSquares:
                    pushForwardOrPushBack(PARAMS, GLOBALVARS, pushSquare, neutralFrontLineID, directionTowardsEnemy)

        else:
            #####NOT EVADING, but maybe too weak, may need backup
            attackingStrength = copy.copy(combineStrength)

            for mySquare in squaresHittingFrontlineList:
                if mySquare.strength > 0:
                    mySquareID = FUNC.getID(mySquare)
                    PARAMS.allMySquares[mySquareID]["attackPower"] = attackingStrength
                    PARAMS.allMySquares[mySquareID]["direction"] = DIR.getDirection(GLOBALVARS, mySquare,neutralFrontLine)

        #####TAKE SQUARES POSSIBLY GOING NEXT TO NEUTRAL FRONT LINE THAT IS NEUTRAL WITH 0 STRENGTH
        for neutralNeighbor in nextNeighborNeutralsWith0:
            neutralNeighborID = FUNC.getID(neutralNeighbor)

            neighbors = GLOBALVARS.game_map.neighbors(neutralNeighbor, n=1, include_self=False)
            for neighbor in neighbors:
                neighborID = FUNC.getID(neighbor)
                if neighbor.owner == PARAMS.myID and PARAMS.allMySquares[neighborID]["accountedForEvading"] == False:
                    neighborTargetSquare = GLOBALVARS.game_map.get_target(neighbor,PARAMS.allMySquares[neighborID]["direction"])
                    neighborTargetSquareID = FUNC.getID(neighborTargetSquare)

                    #logging.debug("%s maybe going to neutral next to frontline.  Its target is: %s \n", neighborID,neighborTargetSquareID)
                    PARAMS.allMySquares[neighborID]["accountedForEvading"] = True
                    if neighborTargetSquareID == neutralNeighborID:
                        #####targets next to neutral frontline
                        if neighbor.strength + attackingStrength > PARAMS.maxStrength:
                            #logging.debug("Going to next to a neutral frontline, keep it still or push: %s \n", neighborID)

                            #####this next neutral is a front line somewhere, may have to push
                            if neutralNeighborID in PARAMS.neutralSquaresInFrontLineIDs:

                                hasEnemy, enemyList, numOfenemies = FUNC.hasEnemyNeighbor(PARAMS, GLOBALVARS, neutralNeighbor)
                                directionTowardsEnemy = DIR.getDirection(GLOBALVARS, neutralNeighbor, enemyList[0])

                                oppositeDirection = (directionTowardsEnemy + 2) % 4
                                #logging.debug("pushing back to direction: %s \n", oppositeDirection)
                                pushSquaresBack(PARAMS, GLOBALVARS, neighbor, oppositeDirection, 1)
                            else:
                                PARAMS.allMySquares[neighborID]["direction"] = STILL
                        else:
                            #####can still combine strength
                            attackingStrength = attackingStrength + neighbor.strength

        #####TAKE SQUARES POSSIBLY GOING TO OUR SQUARE WHICH IS NEXT TO NEUTRAL FRONT LINE
        #####With enemy distance #2
        newTotalStrength = copy.copy(attackingStrength)
        for tempDictionary in squaresWithDistance2:
            for key, value in tempDictionary.items():
                ourSquares = value['square']
                ourSquaresID = FUNC.getID(ourSquares)
                if PARAMS.allMySquares[ourSquaresID]["accountedForEvading"] == False:
                    PARAMS.allMySquares[ourSquaresID]["accountedForEvading"] = True

                    if newTotalStrength + ourSquares.strength <= PARAMS.maxStrength:
                        #####do nothing, keep it going there
                        newTotalStrength = newTotalStrength + ourSquares.strength
                        if newTotalStrength < enemySquare.strength and ourSquares.strength > 0:
                            #####move this square now for back up, unless has 0 strength
                            PARAMS.allMySquares[ourSquaresID]["direction"] = DIR.getDirection(GLOBALVARS, ourSquares, value['target'])
                        else:
                            PARAMS.allMySquares[ourSquaresID]["direction"] = STILL
                    else:
                        PARAMS.allMySquares[ourSquaresID]["direction"] = STILL

################################################################################
#####
################################################################################
def getOurSquaresToFrontLine(PARAMS, GLOBALVARS,neutralFrontLine):
    combineStrength = 0
    squaresWithDistance2 = []
    squareIsHandledBefore = False
    squaresHandledBeforeList = []
    nextNeighborNeutralsWith0 = []
    squaresHittingFrontlineList = []
    neutralFrontLineID = FUNC.getID(neutralFrontLine)
    frontLineNeighbors = GLOBALVARS.game_map.neighbors(neutralFrontLine, n=1, include_self=False)

    for frontlineNeighbor in frontLineNeighbors:
        frontlineNeighborID = FUNC.getID(frontlineNeighbor)

        if frontlineNeighbor.owner == PARAMS.myID and PARAMS.allMySquares[frontlineNeighborID]["accountedForEvading"] == False:
            frontlineNeighborTargetSquare = GLOBALVARS.game_map.get_target(frontlineNeighbor,PARAMS.allMySquares[frontlineNeighborID]["direction"])
            frontlineNeighborTargetSquareID = FUNC.getID(frontlineNeighborTargetSquare)
            #####take squares going to front line or just STILL
            if frontlineNeighborTargetSquareID == neutralFrontLineID or frontlineNeighborTargetSquareID == frontlineNeighborID:
                #####neighbor is going to neutralFrontLineID
                squaresHittingFrontlineList.append(frontlineNeighbor)
                #####Take a zero into account to still know its over 255, to be accounted for evading
                if frontlineNeighbor.strength == 0:
                    combineStrength = combineStrength + frontlineNeighbor.production
                else:
                    combineStrength = combineStrength + frontlineNeighbor.strength

                #####GET OUR SQUARES GOING NEXT TO NEUTRAL FRONT LINE
                #####With enemy distance #2
                nextFrontLineNeighbors = GLOBALVARS.game_map.neighbors(frontlineNeighbor, n=1, include_self=False)
                for nextneighbor in nextFrontLineNeighbors:
                    nextneighborID = FUNC.getID(nextneighbor)
                    if nextneighbor.owner == PARAMS.myID and nextneighborID != frontlineNeighborID:
                        if PARAMS.allMySquares[frontlineNeighborID]["accountedForEvading"] == False:
                            nextneighborTargetSquare = GLOBALVARS.game_map.get_target(nextneighbor, PARAMS.allMySquares[nextneighborID]["direction"])
                            nextneighborTargetSquareID = FUNC.getID(nextneighborTargetSquare)

                            #####take squares going to front line or just STILL
                            if nextneighborTargetSquareID == nextneighborID or nextneighborTargetSquareID == frontlineNeighborID:
                                tempDict = {nextneighborID: {}}
                                tempDict[nextneighborID]['square'] = copy.copy(nextneighbor)
                                tempDict[nextneighborID]['target'] = copy.copy(frontlineNeighbor)
                                squaresWithDistance2.append(tempDict)

        elif frontlineNeighbor.owner == PARAMS.myID and PARAMS.allMySquares[frontlineNeighborID]["accountedForEvading"] == True:
            #####This square has been handled before, keep its direction
            frontlineNeighborID = FUNC.getID(frontlineNeighbor)
            target = GLOBALVARS.game_map.get_target(frontlineNeighbor,PARAMS.allMySquares[frontlineNeighborID]["direction"])
            targetID = FUNC.getID(target)

            if targetID == neutralFrontLineID:
                #####Let this frontline go here and push back rest of the neighboring squares
                squaresHandledBeforeList.append(frontlineNeighbor)
                squareIsHandledBefore = True

        elif frontlineNeighbor.owner == 0 and frontlineNeighbor.strength == 0:
            nextNeighborNeutralsWith0.append(frontlineNeighbor)
        elif frontlineNeighbor.owner == 0:
            doing = None
        else:
            #####Enemy
            enemySquare = copy.copy(frontlineNeighbor)

    return enemySquare, squaresHittingFrontlineList, nextNeighborNeutralsWith0, combineStrength, squaresWithDistance2, squareIsHandledBefore, squaresHandledBeforeList




################################################################################
#####
################################################################################
def pushForwardOrPushBack(PARAMS, GLOBALVARS, pushSquare,neutralFrontLineID,directionTowardsEnemy):
    pushSquareID = FUNC.getID(pushSquare)
    #####Pushing forward
    PARAMS.allMySquares[pushSquareID]["direction"] = copy.copy(directionTowardsEnemy)
    pushTargetSquare = GLOBALVARS.game_map.get_target(pushSquare, directionTowardsEnemy)
    pushTargetSquareID = FUNC.getID(pushTargetSquare)

    if (pushTargetSquare.owner == 0 and pushTargetSquare.strength > 0 and pushSquare.strength < 200) or pushTargetSquareID == neutralFrontLineID:
        #####use push back method
        oppositeDirection = (directionTowardsEnemy + 2) % 4
        pushSquaresBack(PARAMS, GLOBALVARS, pushSquare, oppositeDirection, 1)

    elif pushTargetSquare.owner == 0 and pushTargetSquare.strength > 0 and pushSquare.strength >= PARAMS.minStrengthToEvadePushForwardToNeutral:
        #####Check whether to push forward or back
        hasEnemy, enemyListh, numOfenemies = FUNC.hasEnemyNeighbor(PARAMS, GLOBALVARS,pushTargetSquare)
        if hasEnemy and numOfenemies == 1:
            #####push back
            oppositeDirection = (directionTowardsEnemy + 2) % 4
            pushSquaresBack(PARAMS, GLOBALVARS, pushSquare, oppositeDirection, 1)
        #####else it'll keep it as pushing forward

    else:
        doing = None

################################################################################
#####Will only move 255 or below combine strength, rest will stay STILL (should be safe)
################################################################################
def evadeDistance2ButNoDistance1(PARAMS, GLOBALVARS):
    #####manage neutrals in front line
    for neutralFrontLine in PARAMS.neutralSquaresInFrontLineNextToBorder:
        ourSquaresList = []
        combineStrength = 0
        neutralFrontLineID = FUNC.getID(neutralFrontLine)

        neighbors = GLOBALVARS.game_map.neighbors(neutralFrontLine, n=1, include_self=False)
        for neutral in neighbors:
            if neutral.owner == 0:
                neutralID = FUNC.getID(neutral)
                #####Dont let any other squares go to this neutral spot
                nextNeighbors = GLOBALVARS.game_map.neighbors(neutral, n=1, include_self=False)
                for nextNeighbor in nextNeighbors:
                    nextNeighborID = FUNC.getID(nextNeighbor)
                    if nextNeighbor.owner == PARAMS.myID and PARAMS.allMySquares[nextNeighborID]["accountedForEvading"] == False:
                        nextNeighborTargetSquare = GLOBALVARS.game_map.get_target(nextNeighbor,PARAMS.allMySquares[nextNeighborID]["direction"])
                        nextNeighborTargetSquareID = FUNC.getID(nextNeighborTargetSquare)

                        if nextNeighborTargetSquareID == neutralID:
                            ourSquaresList.append(nextNeighbor)
                            combineStrength = combineStrength + nextNeighbor.strength

        ourSquaresHighToLowList = reversed(sorted(ourSquaresList, key=lambda x: x.strength))
        if combineStrength > PARAMS.maxStrength:
            n = 1
            totalStrength = 0
            for square in ourSquaresHighToLowList:
                squareID = FUNC.getID(square)
                PARAMS.allMySquares[squareID]["accountedForEvading"] = True
                if n == 1:
                    #####Do nothing, let the strongest one go there
                    totalStrength = totalStrength + square.strength
                    n = n + 1
                else:
                    if totalStrength + square.strength > PARAMS.maxStrength:
                        PARAMS.allMySquares[squareID]["direction"] = STILL
                    else:
                        #####Do nothing, let if go there
                        totalStrength = totalStrength + square.strength
                    n = n + 1

################################################################################
#####
################################################################################
def evadeAndPushBack(PARAMS, GLOBALVARS):
    pushBackOurSquaresWithEnemyDistance1(PARAMS,GLOBALVARS)
    getNeighborsOfNeutralBordersCloseToEnemy(PARAMS, GLOBALVARS)
    evadeDistance2ButNoDistance1(PARAMS, GLOBALVARS)
    MG.manageOverStrengthPushed(PARAMS, GLOBALVARS)

################################################################################
#####Only the strongest go to the neutral frontline position
#####The rest are pushed back away from the enemy
################################################################################
def pushBackOurSquaresWithEnemyDistance1(PARAMS, GLOBALVARS):
    #####manage neutrals in front line
    for neutralfrontLine in PARAMS.neutralSquaresInFrontLine:
        frontlineNeighbors = GLOBALVARS.game_map.neighbors(neutralfrontLine, n=1, include_self=False)
        neutralfrontLineID = FUNC.getID(neutralfrontLine)
        numOfOurSquares = 0
        evadingSquaresList = []
        combineStrength = 0
        nextNeighborNeutrals = []

        for neighbor in frontlineNeighbors:
            neighborID = FUNC.getID(neighbor)
            #####only takes into account our squares that are already there
            if neighbor.owner == PARAMS.myID and PARAMS.allMySquares[neighborID]["accountedForEvading"] == False:
                neighborTargetSquare = GLOBALVARS.game_map.get_target(neighbor, PARAMS.allMySquares[neighborID]["direction"])
                neighborTargetSquareID = FUNC.getID(neighborTargetSquare)
                if neighborTargetSquareID == neutralfrontLineID:
                    #####neighbor is going to neutralfrontLineID
                    numOfOurSquares = numOfOurSquares + 1
                    evadingSquaresList.append(neighbor)
                    combineStrength = combineStrength + neighbor.strength
            elif neighbor.owner == 0 and neighbor.strength == 0:
                nextNeighborNeutrals.append(neighbor)
            else:
                #####Enemy
                enemySquare = neighbor

        if combineStrength >= PARAMS.maxStrength and numOfOurSquares > 1:
            #####Try to evade
            directionTowardsEnemy = DIR.getDirection(GLOBALVARS, neutralfrontLine, enemySquare)
            if numOfOurSquares > 1:
                highToLowList = reversed(sorted(evadingSquaresList, key=lambda x: x.strength))
                n = 1
                pushSquares = []
                for square in highToLowList:
                    if n == 1:
                        attackSquare = square
                        n = n + 1
                    else:
                        pushSquares.append(square)
                        n = n + 1
                attackSquareID = FUNC.getID(attackSquare)
                PARAMS.allMySquares[attackSquareID]["accountedForEvading"] = True
                #####direction not changed, should go to the neutral frontline

                for pushSquare in pushSquares:
                    pushSquareID = FUNC.getID(pushSquare)
                    PARAMS.allMySquares[pushSquareID]["accountedForEvading"] = True
                    #####this is for pushing it opposite of the original direction
                    # oldDirection = PARAMS.allMySquares[pushSquareID]["direction"]
                    oppositeDirection = (directionTowardsEnemy + 2) % 4
                    pushSquaresBack(PARAMS, GLOBALVARS, pushSquare, oppositeDirection, 1)

                attackingStrength = attackSquare.strength
        else:
            #####no need to evade
            attackingStrength = combineStrength

        #####take squares possibly going next to neutral front line
        for nextNeighbor in nextNeighborNeutrals:
            nextNeighborID = FUNC.getID(nextNeighbor)
            neighbors = GLOBALVARS.game_map.neighbors(nextNeighbor, n=1, include_self=False)
            for neighbor in neighbors:
                neighborID = FUNC.getID(neighbor)

                if neighbor.owner == PARAMS.myID and PARAMS.allMySquares[neighborID]["accountedForEvading"] == False:
                    neighborTargetSquare = GLOBALVARS.game_map.get_target(neighbor,PARAMS.allMySquares[neighborID]["direction"])
                    neighborTargetSquareID = FUNC.getID(neighborTargetSquare)
                    if neighborTargetSquareID == nextNeighborID:
                        #####targets next to neutral frontline
                        PARAMS.allMySquares[neighborID]["accountedForEvading"] = True
                        if neighbor.strength + attackingStrength > PARAMS.maxStrength:
                            PARAMS.allMySquares[neighborID]["direction"] = STILL
                        else:
                            #####can still combine strength
                            doing = None

################################################################################
#####
################################################################################
def pushSquaresBack(PARAMS, GLOBALVARS, _currentsquare, _pushdirection, _pushedForEvadingNum):
    #####old code
    currentsquare = copy.copy(_currentsquare)
    pushdirection = copy.copy(_pushdirection)
    pushedForEvadingNum = copy.copy(_pushedForEvadingNum)

    currentSquareID = FUNC.getID(currentsquare)
    PARAMS.allMySquares[currentSquareID]["direction"] = pushdirection
    PARAMS.allMySquares[currentSquareID]["accountedForEvading"] = True
    PARAMS.allMySquares[currentSquareID]["pushedForEvading"] = True
    PARAMS.allMySquares[currentSquareID]["pushedForEvadingNum"] = pushedForEvadingNum
    nextSquare = GLOBALVARS.game_map.get_target(currentsquare, pushdirection)

    if nextSquare.owner == PARAMS.myID:
        nextSquareID = FUNC.getID(nextSquare)
        nextSquareDirection = PARAMS.allMySquares[nextSquareID]["direction"]
        #####hard to manage if others are going to this position, might be easier to just always push
        # if nextSquareDirection == (pushdirection + 2)%4 or nextSquareDirection == STILL:
        if currentsquare.strength + nextSquare.strength > PARAMS.maxStrength:
            pushSquaresBack(PARAMS, GLOBALVARS, nextSquare, pushdirection, pushedForEvadingNum + 1)
        else:
            #####not going over, just change its direction to STILL
            PARAMS.allMySquares[nextSquareID]["pushedForEvading"] = True
            PARAMS.allMySquares[nextSquareID]["direction"] = STILL

################################################################################
#####
################################################################################
def getNeighborsOfNeutralBordersCloseToEnemy(PARAMS, GLOBALVARS):
    for namedtple in PARAMS.neutralSquaresInTheBorderWithPriority:
        neutralBorder = namedtple.currentsquare
        neutralBorderID = FUNC.getID(neutralBorder)

        if neutralBorderID not in PARAMS.neutralSquaresInFrontLineIDs:
            neighbors = GLOBALVARS.game_map.neighbors(neutralBorder, n=1,include_self=False)

            for neighbor in neighbors:
                neighborID = FUNC.getID(neighbor)
                hasEnemy, enemyList, numOfenemies = FUNC.hasEnemyNeighbor(PARAMS, GLOBALVARS, neighbor)
                if neighbor.owner == 0 \
                        and neighbor.strength == 0 \
                        and neighborID not in PARAMS.neutralSquaresInFrontLineIDs \
                        and hasEnemy:
                    PARAMS.neutralSquaresInFrontLineNextToBorder.append(neighbor)



