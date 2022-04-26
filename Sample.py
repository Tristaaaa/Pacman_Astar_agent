from functools import update_wrapper
import random
from re import L
import threading
from turtle import down, left, right, up

from pyrsistent import l
import STcpClient
import time
import sys
import numpy as np
import math
from time import time as clock

class MyThread(threading.Thread): 
   def __init__(self, *args, **keywords): 
       threading.Thread.__init__(self, *args, **keywords) 
       self.killed = False      
   def start(self):         
       self.__run_backup = self.run         
       self.run = self.__run                
       threading.Thread.start(self)         
   def __run(self):         
       sys.settrace(self.globaltrace)         
       self.__run_backup()         
       self.run = self.__run_backup         
   def globaltrace(self, frame, event, arg):         
       if event == 'call':             
           return self.localtrace         
       else:             
           return None        
   def localtrace(self, frame, event, arg):         
       if self.killed:             
          if event == 'line':                 
              raise SystemExit()         
       return self.localtrace         
   def kill(self):         
       self.killed = True

pre_pos = (-1, -1)
pre_dir = -1
cnt = 0
mine = 0

class cell:
    def __init__(self):
        # Row and Column index of its parent
        # Note that 0 <= i <= ROW-1 & 0 <= j <= COL-1
        self.parent_i = -1
        self.parent_j = -1
        self.dir = -1
        # f = g + h
        self.f = -1
        self.g = -1
        self.h = -1
        #self.time = -1

def isValid16(row, col) -> bool:
    return (row >= 0) & (row < 16) & (col >= 0) & (col < 16) 
 
 
# A Utility Function to check whether the given cell is blocked or not
def isUnBlocked(row, col, direc) -> bool:
    # Returns true if the cell is not blocked else false

    if direc == 2:
        if parallel_wall[row][col] == 1:
            return False
        return True
    elif direc == 3:
        if parallel_wall[row][col + 1] == 1:
            return False
        return True
    elif direc == 0:
        if vertical_wall[row][col] == 1:
            return False
        return True
    elif direc == 1:
        if vertical_wall[row + 1][col] == 1:
            return False
        return True

# A Utility Function to check whether destination cell has been reached or not
def isDestination(dist, row, col, dest, propsh, dst_):
    #if (row == dest[0]) & (col == dest[1]):
    if (row, col) in dest:
        val = propsh[tuple([row, col])]
        if ((val[1] * val[2] / pow(dist, 2)) >= (propsh[dst_][1] * propsh[dst_][2] / pow(dist, 2))):
            return True
        else:
            return False
    else:
        return False
 
# A Utility Function to calculate the 'h' heuristics.
def calculateHValue(row, col,  dest) -> float:
    # Return using the distance formula
    return (abs(row - dest[0]) + abs(col - dest[1]))
 
# A Utility Function to trace the path from the source to destination
def tracePath(cellDetails, dest) -> tuple:
    #printf("\nThe Path is ")
    row = dest[0]
    col = dest[1]
    direc = 0
    #stack<Pair> Path
    #print("trace path start")
    while (not ((cellDetails[row][col].parent_i == row) & (cellDetails[row][col].parent_j == col))):
        #Path.push(make_pair(row, col))
        next_row = row
        next_col = col
        row = cellDetails[next_row][next_col].parent_i
        col = cellDetails[next_row][next_col].parent_j
        direc = cellDetails[next_row][next_col].dir
        #print(row, " ", col)
        #print("dir, ", direc)
    #print("direc:", direc)
    #Path.push(make_pair(row, col))
    #while (not Path.empty()) :
    #    pair<int, int> p = Path.top()
    #    Path.pop()
    #    printf("-> (%d,%d) ", p.first, p.second)
 
    return direc

def propsHeuristic(playerStat, propsStat) -> tuple:
    dist = {}
    player_i = int(playerStat[0]/25)
    player_j = int(playerStat[1]/25)

    # 0: landmine
    props0 = [(int(x/25), int(y/25)) for type, x, y in propsStat if type == 0]
    for i in range(np.shape(props0)[0]):
        d = abs(player_i - props0[i][0]) + abs(player_j - props0[i][1])
        if (d < 1):
            d = 1
        dist[tuple([props0[i][0], props0[i][1]])] = [d, 5, 1]
    
    # 1: power
    props1 = [(int(x/25), int(y/25)) for type, x, y in propsStat if type == 1]
    for i in range(np.shape(props1)[0]):
        d = abs(player_i - props1[i][0]) + abs(player_j - props1[i][1])
        if (d < 1):
            d = 1
        if (playerStat[3] > 100): 
            dist[tuple([props1[i][0], props1[i][1]])] = [d, 200, 1]
        else:
            dist[tuple([props1[i][0], props1[i][1]])] = [d, 3000, 1]

    # 2: pellet
    props2 = [(int(x/25), int(y/25)) for type, x, y in propsStat if type == 2]
    for i in range(np.shape(props2)[0]):
        d = abs(player_i - props2[i][0]) + abs(player_j - props2[i][1])
        if (d < 1):
            d = 1
        group = [(int(x/25), int(y/25)) for type, x, y in propsStat if ((type == 2) and ((abs(int(x/25) - props2[i][1]) + abs(int(y/25) - props2[i][1])) <= 2))]
        dist[tuple([props2[i][0], props2[i][1]])] = [d, 10, np.shape(group)[0] / 1.5]

    if (playerStat[3] > 5):
        # ghost:
        four_dir = [[-1, 0], [1, 0], [0, -1], [0, 1]]
        ghost = [(int(x/25), int(y/25)) for x, y in ghostStat]
        for i in range(np.shape(ghost)[0]):
            if not ((ghost[i] == (7, 7)) or (ghost[i] == (7, 8)) or (ghost[i] == (8, 7)) or (ghost[i] == (8, 8))):
                d = abs(player_i - ghost[i][0]) + abs(player_j - ghost[i][1])
                if (d < 1):
                    d = 1
                dist[tuple([ghost[i][0], ghost[i][1]])] = [d, 400, 1]
            for j in range(4):
                if isValid16(ghost[i][0] + four_dir[j][0], ghost[i][0] + four_dir[j][1]) and isUnBlocked(ghost[i][0], ghost[i][1], j) and (not((((ghost[i][0] + four_dir[j][0]) == 7) or ((ghost[i][0] + four_dir[j][0]) == 8)) and (((ghost[i][0] + four_dir[j][1]) == 7) or ((ghost[i][0] + four_dir[j][1]) == 8)))):
                    d = abs(player_i - (ghost[i][0] + four_dir[j][0])) + abs(player_j - (ghost[i][0] + four_dir[j][1]))
                    if (d < 1):
                        d = 1
                    dist[tuple([ghost[i][0] + four_dir[j][0], ghost[i][0] + four_dir[j][1]])] = [d, 400, 1]


    #dist = dict(sorted(dist.items(), key=lambda x: x[1]))
    key_max = max(dist.keys(), key=(lambda k: dist[k][1] * dist[k][2] / pow(dist[k][0], 1.5)))
    return key_max, dist

def danger(playerStat, ghostStat, propsStat, round):
    # 3: bomb
    four_dir = [[-1, 0], [1, 0], [0, -1], [0, 1]]
    diag_dir = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
    danger_pos = [(x, y) for type, x, y in propsStat if type == 3]
    for i in range(np.shape(danger_pos)[0]):
        actu_x = danger_pos[i][0]
        actu_y = danger_pos[i][1]
        danger_pos[i] = (int(danger_pos[i][0]/25), int(danger_pos[i][1]/25))
        for j in range(4):
            if (int((actu_x + 12 * four_dir[j][0])/25), int((actu_y + 12 * four_dir[j][1])/25)) not in danger_pos:
                danger_pos.append((int((actu_x + 12 * four_dir[j][0])/25), int((actu_y + 12 * four_dir[j][1])/25)))
        for j in range(4):
            if (int((actu_x + 6 * diag_dir[j][0])/25), int((actu_y + 6 * diag_dir[j][1])/25)) not in danger_pos:
                danger_pos.append((int((actu_x + 6 * diag_dir[j][0])/25), int((actu_y + 6 * diag_dir[j][1])/25)))
        #tmp_i = int(danger_pos[i][0]/25)
        #tmp_j = int(danger_pos[i][1]/25)
        #eight_dir = [[-1,-1], [0,-1], [1,-1], [-1,0], [1,0], [-1,1], [0,1],[1,1]]
        #for j in range(8):
        #    if abs(danger_pos[i][0] - ((tmp_i + eight_dir[j][0])*25+12)) + abs(danger_pos[i][1] - ((tmp_j + eight_dir[j][1])*25+12)) <= 12:
        #        if isValid16(tmp_i + eight_dir[j][0], tmp_j + eight_dir[j][1]):
        #            danger_pos.append((tmp_i + eight_dir[j][0], tmp_j + eight_dir[j][1]))
    
    if (playerStat[3] > 5):
        return danger_pos
    
    #avoid ghost
    dist = [0, 0, 0, 0]
    for i in range(4):
        dist[i] = abs(ghostStat[i][0] - playerStat[0]) + abs(ghostStat[i][1]- playerStat[1])
        if not(((int(ghostStat[i][0]/25) == 7) or (int(ghostStat[i][0]/25) == 8)) and ((int(ghostStat[i][1]/25) == 7) or (int(ghostStat[i][1]/25) == 8))):
            danger_pos.append((int(ghostStat[i][0]/25), int(ghostStat[i][1]/25)))

    four_dir = [[-1, 0], [1, 0], [0, -1], [0, 1]]
    for i in range(4):
        ghost_i = int(ghostStat[i][0]/25)
        ghost_j = int(ghostStat[i][1]/25)
        for j in range(4):
            if isValid16(ghost_i + four_dir[i][0], ghost_j + four_dir[j][1]) and isUnBlocked(ghost_i, ghost_j, j) and (not((((ghost_i + four_dir[j][0]) == 7) or ((ghost_i + four_dir[j][0]) == 8)) and (((ghost_i + four_dir[j][1]) == 7) or ((ghost_i + four_dir[j][1]) == 8)))):
                danger_pos.append((ghost_i + four_dir[j][0], ghost_j + four_dir[j][1]))
                if (round <= 1) and (dist[i] > 40) and isValid16(ghost_i + 2 * four_dir[j][0], ghost_j + 2 * four_dir[j][1]) and isUnBlocked(ghost_i + four_dir[j][0], ghost_j + four_dir[j][1], i) and (not((((ghost_i + 2 * four_dir[j][0]) == 7) or ((ghost_i + 2 * four_dir[j][0]) == 8)) and (((ghost_i + 2 * four_dir[j][1]) == 7) or ((ghost_i + 2 * four_dir[j][1]) == 8)))):
                    danger_pos.append((ghost_i + 2 * four_dir[j][0], ghost_j + 2 * four_dir[j][1]))
    if (round >= 2):
        return danger_pos

    diag = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
    check = [[0, 2], [0, 3], [1, 2], [1, 3]]
    for i in range(4):
        if dist[i] > 25:
            ghost_i = int(ghostStat[i][0]/25)
            ghost_j = int(ghostStat[i][1]/25)
            for j in range(4):
                if isValid16(ghost_i + diag[j][0], ghost_j + diag[j][1]) and (isUnBlocked(ghost_i, ghost_j, check[j][0]) or isUnBlocked(ghost_i, ghost_j, check[j][1])) and (not((((ghost_i + diag[j][0]) == 7) or ((ghost_i + diag[j][0]) == 8)) and (((ghost_i + diag[j][1]) == 7) or ((ghost_i + diag[j][1]) == 8)))):
                    danger_pos.append((ghost_i + four_dir[j][0], ghost_j + four_dir[j][1]))
    #print(danger_pos)
    return danger_pos

def findDST(playerStat, ghostStat, propsStat, dst_, propsh):
        # If the source is out of range
    '''if (isValid(playerStat[0], playerStat[1], cur_dir, playerStat[3]) == False):
        print("Source is invalid\n")
        return -1'''
    global pre_dir
    dst = [(int(x/25), int(y/25)) for type, x, y in propsStat if ((type == 0) or (type == 1) or (type == 2))]
    if playerStat[3] > 5:
        four_dir = [[-1, 0], [1, 0], [0, -1], [0, 1]]
        for i in range(4):
            if not(((int(ghostStat[i][0]/25) == 7) or (int(ghostStat[i][0]/25) == 8)) and ((int(ghostStat[i][1]/25) == 7) or (int(ghostStat[i][1]/25) == 8))):
                dst.append((int(ghostStat[i][0]/25), int(ghostStat[i][1]/25)))
            for j in range(4):
                if not(((int((ghostStat[i][0] + four_dir[j][0])/25) == 7) or (int((ghostStat[i][0] + four_dir[j][0])/25) == 8)) and ((int((ghostStat[i][1] + four_dir[j][1])/25) == 7) or (int((ghostStat[i][1] + four_dir[j][1])/25) == 8))):
                    dst.append((int((ghostStat[i][0] + four_dir[j][0])/25), int((ghostStat[i][1] + four_dir[j][1])/25)))

    danger_pos = danger(playerStat, ghostStat, propsStat, 0)
    # Create a closed list and initialise it to false which means that no cell has been included yet This closed list is implemented as a boolean 2D array
    closedList = np.zeros((16, 16), dtype=int)
 
    # Declare a 2D array of structure to hold the details of that cell
    cellDetails = np.zeros((16, 16), dtype=cell)

    for i in range(16):
        for j in range(16):
            cellDetails[i][j] = cell()

 
    # Initialising the parameters of the starting node
    i = int(playerStat[0] / 25)
    j = int(playerStat[1] / 25)
    cellDetails[i][j].f = 0.0
    cellDetails[i][j].g = 0.0
    cellDetails[i][j].h = 0.0
    cellDetails[i][j].parent_i = i
    cellDetails[i][j].parent_j = j
    cellDetails[i][j].dir = pre_dir
    #cellDetails[i][j].time = 0
 
    '''
     Create an open list having information as-
     <f, <i, j>>
     where f = g + h,
     and i, j are the row and column index of that cell
     Note that 0 <= i <= ROW-1 & 0 <= j <= COL-1
     This open list is implemented as a set of pair of
     pair.'''
    openList = {}
 
    # Put the starting cell on the open list and set its 'f' as 0
    openList[tuple([i, j])] = 0
 
    # We set this boolean value as false as initially the destination is not reached.
    foundDest = False


    #0: left, 1:right, 2: up, 3: down 4:no control
    #dirs = [0, 1, 2, 3]
    four_dir = [[-1, 0], [1, 0], [0, -1], [0, 1]]
    while (openList) :
        # Add this vertex to the closed list
        i = list(openList.keys())[0][0]
        j = list(openList.keys())[0][1]
        d = cellDetails[i][j].dir
        #print("\n")
        #print(i, " ", j)
        ops = -1
        if d == 0:
            ops = 1
        elif d == 1:
            ops = 0
        elif d == 2:
            ops = 3
        elif d == 3:
            ops = 2
        # Remove this vertex from the open list
        del openList[list(openList.keys())[0]]
        closedList[i][j] = 1
        #s_time = cellDetails[i][j].g
        '''if time < s_time:
            step = 8
        else:
            step = 5
        '''
        for k in range(4):
            if k == ops:
                continue
            #print(d, " ", ops)
            if isValid16(i + four_dir[k][0], j + four_dir[k][1]) and isUnBlocked(i, j, k):
                #print(i, " ", j, " ", k)
                if (i + four_dir[k][0], j + four_dir[k][1]) in danger_pos:
                    #print("dangerous place: ", i + four_dir[k][0], j + four_dir[k][1])
                    continue
                # If the destination cell is the same as the current successor
                if dst_ == (i + four_dir[k][0], j + four_dir[k][1]):
                    cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].parent_i = i
                    cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].parent_j = j
                    cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].dir = k
                    #print("dst: ", dst_)
                    return cellDetails, dst_
                elif isDestination(cellDetails[i][j].g + 1.0, i + four_dir[k][0], j + four_dir[k][1], dst, propsh, dst_):
                    # Set the Parent of the destination cell
                    #print("found dst!!!!!!!")
                    cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].parent_i = i
                    cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].parent_j = j
                    cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].dir = k
                    #printf("The destination cell is found\n");
                    dst_ = (i + four_dir[k][0], j + four_dir[k][1])
                    return findDST(playerStat, ghostStat, propsStat, dst_, propsh)
                    #print("dst: ", dst)
                    foundDest = True

                # If the successor is already on the closed
                # list or if it is blocked, then ignore it.
                # Else do the following
                elif (closedList[i + four_dir[k][0]][j + four_dir[k][1]] == False):
                    gNew = cellDetails[i][j].g + 1.0
                    hNew = calculateHValue(i + four_dir[k][0], j + four_dir[k][1], dst_)
                    fNew = gNew + hNew
    
                    ''' If it isn’t on the open list, add it to
                    // the open list. Make the current square
                    // the parent of this square. Record the
                    // f, g, and h costs of the square cell
                    //                OR
                    // If it is on the open list already, check
                    // to see if this path to that square is
                    // better, using 'f' cost as the measure.'''
                    if (cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].f == -1) or (cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].f > fNew):
                        openList[tuple([i + four_dir[k][0], j + four_dir[k][1]])] = fNew
                        # Update the details of this cell
                        cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].f = fNew
                        cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].g = gNew
                        cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].h = hNew
                        cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].parent_i = i
                        cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].parent_j = j
                        cellDetails[i + four_dir[k][0]][j + four_dir[k][1]].dir = k
        openList = dict(sorted(openList.items(), key=lambda x: x[1]))
    #print("can't find a destination!")
    return cellDetails, (-1, -1)

def aStarSearch(playerStat, ghostStat, propsStat) -> int:
    global pre_dir

    dst_, propsh = propsHeuristic(playerStat, propsStat)
    if playerStat == None:
        print("playerStat is NONE!!!!")
    elif ghostStat == None:
        print("ghostStat is NONE!!!!")
    elif propsStat == None:
        print("propsStat is NONE!!!!")
    elif dst_ == None:
        print("DST is NONE!!!!")
    #print("new time step!!!")
    cellDetails, dst = findDST(playerStat, ghostStat, propsStat, dst_, propsh)
    if dst == (-1, -1):
        four_dir = [[-1, 0], [1, 0], [0, -1], [0, 1]]
        danger_pos = danger(playerStat, ghostStat, propsStat, 0)
        round = 1
        while (1):
            option = [0, 1, 2, 3]
            while (option):
                move = random.choice(option)
                ops = -1
                if pre_dir == 0:
                    ops = 1
                elif pre_dir == 1:
                    ops = 0
                elif pre_dir == 2:
                    ops = 3
                elif pre_dir == 3:
                    ops = 2
                if (move != ops) and isValid16(int(playerStat[0]/25) + four_dir[move][0], int(playerStat[1]/25) + four_dir[move][1]) and isUnBlocked(int(playerStat[0]/25), int(playerStat[1]/25), move) and ((int(playerStat[0]/25) + four_dir[move][0], int(playerStat[1]/25) + four_dir[move][1]) not in danger_pos):
                    return move
                option.remove(move)
            danger_pos = danger(playerStat, ghostStat, propsStat, round)
            round += 1
    move = tracePath(cellDetails, dst)
    return move


def getStep(playerStat, ghostStat, propsStat):
    global action, pre_dir, pre_pos, cnt
    '''
    control of your player
    0: left, 1:right, 2: up, 3: down 4:no control
    format is (control, set landmine or not) = (0~3, True or False)
    put your control in action and time limit is 0.04sec for one step
    '''
    start = clock()

    
    if pre_pos != (-1, -1):
        change_i = playerStat[0] - pre_pos[0]
        change_j = playerStat[1] - pre_pos[1]
        #print("change: ", change_i, change_j)
        if change_i < -2:
            pre_dir = 0
        elif change_i > 2:
            pre_dir = 1
        elif change_j < -2:
            pre_dir = 2
        elif change_j > 2:
            pre_dir = 3
        else:
            cnt += 1
    if cnt >= 2:
        if pre_dir == 0:
            pre_dir = 1
        elif pre_dir == 1:
            pre_dir = 0
        elif pre_dir == 2:
            pre_dir = 3
        elif pre_dir == 3:
            pre_dir = 2
        else:
            pre_dir = -1
        cnt = 0

    pre_pos = (playerStat[0], playerStat[1])
    #move = random.choice([0, 1, 2, 3, 4]) 
    #print(len(propsStat))
    #print(int(playerStat[0] / 25), " ", int(playerStat[1] / 25))

    #print("previous direction: ", pre_dir)

    move = aStarSearch(playerStat, ghostStat, propsStat)
    #if move != pre_dir:
    #    stop = 1
    #print(cur_dir, movement)
    '''if movement == -1:
        movement = cur_dir'''
    #print("move:", move)
    pre_dir = move

    global mine
    landmine = False
    if mine > 5:
        mine = 0
    elif mine > 0:
        mine += 1
    if (playerStat[2] > 0) and (mine == 0):
        if playerStat[3] <= 0:
            for i in range(np.shape(ghostStat)[0]):
                if (abs(int(playerStat[0]/25) - int(ghostStat[i][0]/25)) + abs(int(playerStat[1]/25) - int(ghostStat[i][1]/25))) <= 2:
                    landmine = True
                    mine = 1
                    break
        for i in range(np.shape(otherPlayerStat)[0]):
            if (abs(int(playerStat[0]/25) - int(otherPlayerStat[i][0]/25)) + abs(int(playerStat[1]/25) - int(otherPlayerStat[i][1]/25))) <= 2:
                landmine = True
                mine = 1
                break
        #landmine = random.choice([True, False])
    spend = clock() - start
    #print("spend: ", spend)
    action = [move, landmine]


# props img size => pellet = 5*5, landmine = 11*11, bomb = 11*11
# player, ghost img size=23x23


if __name__ == "__main__":
    # parallel_wall = zeros([16, 17])
    # vertical_wall = zeros([17, 16])
    (stop_program, id_package, parallel_wall, vertical_wall) = STcpClient.GetMap()


    while True:
        # playerStat: [x, y, n_landmine,super_time, score]
        # otherplayerStat: [x, y, n_landmine, super_time]
        # ghostStat: [[x, y],[x, y],[x, y],[x, y]]
        # propsStat: [[type, x, y] * N]
        (stop_program, id_package, playerStat,otherPlayerStat, ghostStat, propsStat) = STcpClient.GetGameStat()
        if stop_program:
            break
        elif stop_program is None:
            break
        global action
        action = None
        user_thread = MyThread(target=getStep, args=(playerStat, ghostStat, propsStat))
        user_thread.start()
        time.sleep(4/100)
        if action == None:
            user_thread.kill()
            user_thread.join()
            action = [4, False]
        is_connect=STcpClient.SendStep(id_package, action[0], action[1])
        if not is_connect:
            break
