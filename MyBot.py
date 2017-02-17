import hlt
import logging
import copy
import time
import MyBotData as D
import MyBotGatherData as GD
import MyBotFunctions as FUNC
import MyBotManage as MG
import MyBotExpand as EXP
import MyBotAttack as ATK
import MyBotEvade as EV
import MyBotDirections as DIR
import MyBotInit as INIT

if __name__ == '__main__':

    myID, game_map = hlt.get_init()
    GLOBALVARS = D.GlobalParameters(game_map)
    logging.basicConfig(filename='1example.log', level=logging.DEBUG)

    #INIT.initialize(GLOBALVARS,myID)
    hlt.send_init("En3rG_v2.46")

    while True:

        GLOBALVARS.game_map.get_frame()

        moves = []
        PARAMS = D.Parameters(myID, GLOBALVARS.maxturns)
        D.updateParamsPerMap(PARAMS, GLOBALVARS)

        GD.getSquaresInfo(PARAMS, GLOBALVARS)

        FUNC.setRequestHelpPriority(PARAMS, GLOBALVARS)

        GD.getNeutralSquaresDetectedEnemy(PARAMS, GLOBALVARS)

        if GLOBALVARS.hasEnemyBeenEngaged == False \
                and GLOBALVARS.hasEnemyBeenDetected == False \
                and GLOBALVARS.initExpand == True:
            INIT.expand(PARAMS,GLOBALVARS)
        else:
            FUNC.attackAndExpand(PARAMS,GLOBALVARS)
            DIR.updateDirectionOfMiddleSquares(PARAMS, GLOBALVARS)

        EV.evadeTowardsEnemy(PARAMS, GLOBALVARS)
        #EV.evadeAndPushBack(PARAMS, GLOBALVARS)

        FUNC.setTarget(PARAMS, GLOBALVARS)

        MG.manageOverStrengthDirection(PARAMS, GLOBALVARS)
        MG.manageOverStrengthDirectionSelfTargets(PARAMS)
        MG.manageOverStrengthDirectionSwapPosition(PARAMS, GLOBALVARS)
        MG.swap2with1(PARAMS, GLOBALVARS)

        moves = DIR.setDirections(PARAMS, moves)
        hlt.send_frame(moves)
        GLOBALVARS.OLDPARAMS = copy.copy(PARAMS)

        GLOBALVARS.turn = GLOBALVARS.turn + 1
