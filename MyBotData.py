import math
import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square

################################################################################
#####
#####starting_EnemySquares: {'enemy square ID : square}
#####starting_NeutralSquares: {'neutral square ID : StartingNeutralTemplate}
################################################################################
class GlobalParameters():
    def __init__(self,game_map):
        self.maxturns = 10 * math.sqrt(game_map.width * game_map.height)
        self.turn = -1
        self.OLDPARAMS = None
        self.hasEnemyBeenEngaged = False
        self.hasEnemyBeenDetected = False #####Set to True in INIT
        self.initExpand = False
        self.game_map = game_map
        self.closestEnemySquare = None
        self.starting_MySquare = None
        self.starting_EnemySquares = {}
        self.starting_NeutralSquares = {}
        self.starting_AllSquares = {}
        self.neutralRatioArea = 2
        self.numOfSquaresInLineINIT = 11
        self.bestLineOfAttackList = None
        self.directions = {}

        self.useINITAreaRatio = False
        self.minSquareStrengthBeforeMovingMiddleINITLine = 20

################################################################################
#####
################################################################################
class StartingNeutralTemplate():
    def __init__(self):
        self.dict = {'currentsquare': None,
                     'ratio': 0,
                     'areaRatio': 0}

################################################################################
#####neutralExpandingTargets: {'main neutral target ID': NeutralTargetTemplate}
#####allMySquares: {'my square ID' : MySquaresTemplate}
#####allNeutralSquares: {'neutral ID' : {'currentsquare': , 'ratio':}}

################################################################################
class Parameters():
    def __init__(self,myID,maxturns):
        self.distanceFromEnemyStartPoweringUp = 2
        self.poweringBackUpNum = 4
        self.minSquareStrengthPoweringUp = 30
        self.minSquareStrengthPoweringUp_1 = 150
        self.callForBackupNum = 5
        self.maxDistanceFromMiddleToEnemy = 7
        self.minSquareStrengthBeforeMoving = 25
        self.forceMinStrengthForExpanding = 1
        self.maxDistanceFromMiddleToStayTime = 6
        self.turnsToStayBeforeMoving = 6
        self.strengthToForceMove_2 = 300
        self.strengthToForceMove_4 = 30
        self.requestHelpPriorityPercent = 0.99
        self.preventAttackingFirst = True

        self.createOpeningDistanceFromEnemy = 3
        self.minStrengthCreateOpening = 200
        self.minStrengthToEvadePushForwardToNeutral = 200
        self.minStrengthToAttackNeutralEnemyDetected = 250
        self.openingGameTurns =0.0000*maxturns
        self.myID = myID
        self.minProductionToStay = 1
        self.maxStrength = 255
        self.neutralRatioArea = 2
        self.neutralRatioLine = 2

        self.managedTargetIDs = []
        self.managedDontSwapAnymoreID = []

        self.neutralSquaresInFrontLine = []
        self.neutralSquaresInFrontLineIDs = []
        self.neutralSquaresDetectedEnemy = []
        self.neutralSquaresInTheBorderWithPriority = []
        self.neutralSquaresInFrontLineNextToBorder = []
        self.neutralExpandingTargets = {}
        self.deletedFromExpandingSquaresID = []

        self.accountedIDsToAttack = []

        self.enemyTargetDict = {}
        self.enemyTargetList = []
        self.enemyTargetIDs = []

        self.mySquaresAlongEnemyBorder = {}

        self.allMySquares = {}
        self.allMySquaresList = []
        self.allNeutralSquares = {}
        self.allNeutralSquaresList = []

################################################################################
#####neighbors: {'north':{'square':XXXXX, 'neighborPriority':XXXX}} for all directions
################################################################################
class MySquaresTemplate():
    def __init__(self):
        self.dict = {'currentsquare': None,
                     'neighbors':{},
                      'direction': STILL,
                      'requestHelpPriority':0,
                      'enemy_Distance': 0,
                      'enemy_Distance-1': 0,
                      'enemy_NextSquare': None,
                      'enemy_NextSquare-1': None,
                      'enemy_TargetSquare': None,
                      'expanding_Distance': 0,
                      'expanding_NextSquare': None,
                      'expanding_TargetSquare': None,
                      'desired_TowardID': None,
                      'actual_TowardID': None,
                      'possibleSwap': False,
                      'temp_selftarget':False,
                      'fakeEnemy_Distance': 0,
                      'fakeEnemy_NextSquare': None,
                      'fakeEnemy_TargetSquare': None,
                      'pushedForEvading': False,
                      'pushedForEvadingNum': 0,
                      'attackPower': 0,
                      'accountedForEvading': False}

################################################################################
#####
################################################################################
class NeutralTemplate():
    def __init__(self):
        self.dict = {'currentsquare': None,
                     'ratio': 0}

################################################################################
#####attackingSquare: { 'distance number': [ list of squares ] }
################################################################################
class NeutralTargetTemplate():
    def __init__(self,mainTargetID,mainTargetSq,moveDistance):
        self.dict = {'id': mainTargetID,
                     'currentsquare': mainTargetSq,
                     'expandingSquares': {},
                     'moveSquareWithDistance': moveDistance}

################################################################################
#####
################################################################################
def updateParamsPerMap(PARAMS,GLOBALVARS):
    earlyGame = int(GLOBALVARS.maxturns * (0.38))
    midGame = int(GLOBALVARS.maxturns * (0.65))

    #####if 20x20 or below
    if GLOBALVARS.maxturns < 241:
        PARAMS.distanceFromEnemyStartPoweringUp = 3
        PARAMS.poweringBackUpNum = 4
        PARAMS.minSquareStrengthPoweringUp = 50
        PARAMS.minSquareStrengthPoweringUp_1 = 150
        PARAMS.callForBackupNum = 5
        PARAMS.maxDistanceFromMiddleToEnemy = 50
        PARAMS.minSquareStrengthBeforeMoving = 30
        PARAMS.forceMinStrengthForExpanding = 1
        PARAMS.maxDistanceFromMiddleToStayTime = 50
        PARAMS.turnsToStayBeforeMoving = 8
        PARAMS.strengthToForceMove_2 = 300
        PARAMS.strengthToForceMove_4 = 30
        PARAMS.requestHelpPriorityPercent = 0.99
        PARAMS.preventAttackingFirst = False

        if GLOBALVARS.hasEnemyBeenEngaged == True:
            PARAMS.forceMinStrengthForExpanding = 20

    #####if 30x30 or below
    elif GLOBALVARS.maxturns < 351:
        PARAMS.distanceFromEnemyStartPoweringUp = 2
        PARAMS.poweringBackUpNum = 3
        PARAMS.minSquareStrengthPoweringUp = 50
        PARAMS.minSquareStrengthPoweringUp_1 = 75
        PARAMS.callForBackupNum = 6
        PARAMS.maxDistanceFromMiddleToEnemy = 50
        PARAMS.minSquareStrengthBeforeMoving = 30
        PARAMS.forceMinStrengthForExpanding = 1
        PARAMS.maxDistanceFromMiddleToStayTime = 50
        PARAMS.turnsToStayBeforeMoving = 8
        PARAMS.strengthToForceMove_2 = 300
        PARAMS.strengthToForceMove_4 = 30
        PARAMS.requestHelpPriorityPercent = 0.99
        PARAMS.preventAttackingFirst = True

        if GLOBALVARS.hasEnemyBeenEngaged == True:
            PARAMS.forceMinStrengthForExpanding = 1

    else:
        PARAMS.distanceFromEnemyStartPoweringUp = 2
        PARAMS.poweringBackUpNum = 3
        PARAMS.minSquareStrengthPoweringUp = 50
        PARAMS.minSquareStrengthPoweringUp_1 = 75
        PARAMS.callForBackupNum = 6
        PARAMS.maxDistanceFromMiddleToEnemy = 7 #####not really used, only till 35x35
        PARAMS.minSquareStrengthBeforeMoving = 30
        PARAMS.forceMinStrengthForExpanding = 1
        PARAMS.maxDistanceFromMiddleToStayTime = 50
        PARAMS.turnsToStayBeforeMoving = 8
        PARAMS.strengthToForceMove_2 = 300
        PARAMS.strengthToForceMove_4 = 30
        PARAMS.requestHelpPriorityPercent = 0.99
        PARAMS.preventAttackingFirst = True

        if GLOBALVARS.hasEnemyBeenEngaged == True:
            PARAMS.forceMinStrengthForExpanding = 1


