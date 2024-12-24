# (c) Will Morrow Dec 2024
# See LICENSE file in this repo for limitations and conditions
#!/usr/bin/env python3
import argparse, enum, random, textwrap

class MazeOpening(enum.IntFlag):
    NORTH = enum.auto()
    EAST = enum.auto()
    SOUTH = enum.auto()
    WEST = enum.auto()

    @classmethod
    def opposite(cls, direction):
        match direction:
            case cls.NORTH:
                return cls.SOUTH
            case cls.EAST:
                return cls.WEST
            case cls.SOUTH:
                return cls.NORTH
            case cls.WEST:
                return cls.EAST
            case _:
                return MazeOpening(0)

class MazeCell(object):
    def __init__(self, openings=None):
        if openings is None:
            self._openings = MazeOpening(0)
        else:
            self._openings = openings

    def getOpenings(self):
        return self._openings

    def block(self, blockFrom):
        if blockFrom is None or blockFrom == 0:
            raise Exception('Must block from at least one direction')
        self._openings = self._openings & (~blockFrom)

    def carve(self, openFrom):
        if openFrom is None or openFrom == 0:
            raise Exception('Must open from at least one direction')
        self._openings = self._openings | openFrom

class MazeDefinition(object):
    def __init__(self, width, height, allowWrapX=None, allowWrapY=None):
        if width is None or height is None:
            raise Exception('Must define both width and height')
        self._width = width
        self._height = height
        self._allowWrapX = False if allowWrapX is None else allowWrapX
        self._allowWrapY = False if allowWrapY is None else allowWrapY
        self._cells = [[MazeCell() for y in range(height)] for x in range(width)]
        self._start = (0, 0)
        self._end = (0, 0)

    def getSize(self):
        return (self._width, self._height)

    def getStart(self):
        return self._start

    def getEnd(self):
        return self._end

    def setStart(self, x, y):
        if (x < 0) or (y < 0) or (x >= self._width) or (y >= self._height):
            raise Exception('Out of bounds')
        self._start = (x, y)

    def setEnd(self, x, y):
        if (x < 0) or (y < 0) or (x >= self._width) or (y >= self._height):
            raise Exception('Out of bounds')
        self._end = (x, y)

    def wrap(self, val, delta, limit):
        if not (delta == -1 or delta == 1):
            raise Exception('Delta must be -1 or 1')
        if val == 0 and delta < 0:
            return limit-1
        if val == limit-1 and delta > 0:
            return 0
        return val + delta

    def carve(self, x, y, direction):
        if direction is None or direction == 0:
            raise Exception('Must open at least one direction')
        if (x < 0) or (y < 0) or (x >= self._width) or (y >= self._height):
            raise Exception('Out of bounds')
        oobException = Exception('Cannot open to out of bounds')
        if (x == 0 and MazeOpening.WEST in direction and not self._allowWrapX):
            raise oobException
        if (x == self._width-1 and MazeOpening.EAST in direction and not self._allowWrapX):
            raise oobException
        if (y == 0 and MazeOpening.NORTH in direction and not self._allowWrapY):
            raise oobException
        if (y == self._height-1 and MazeOpening.SOUTH in direction and not self._allowWrapY):
            raise oobException
        # Note here that opening is the direction that the cell at (x, y) will be opening, so we need to open the opposite on every adjacent cell
        self._cells[x][y].carve(direction)
        for opening in list(direction):
            otherCell = None
            otherDirection = MazeOpening.opposite(opening)
            match opening:
                case MazeOpening.NORTH:
                    otherCell = self._cells[x][self.wrap(y, -1, self._height)]
                case MazeOpening.EAST:
                    otherCell = self._cells[self.wrap(x, 1, self._width)][y]
                case MazeOpening.SOUTH:
                    otherCell = self._cells[x][self.wrap(y, 1, self._height)]
                case MazeOpening.WEST:
                    otherCell = self._cells[self.wrap(x, -1, self._width)][y]
            if otherCell is None:
                raise Exception('Didn\'t find other cell when looking for {:s} at (:d, :d)'.format(opening, x, y))
            otherCell.carve(otherDirection)

    def getCells(self):
        return self._cells

class MazePrinter(object):
    def print(self, mazeDefinition):
        raise Exception('Not implemented')

class MazeGenerator(object):
    def generate(self, width, height, seed):
        raise Exception('Not implemented')

class VerbosePrintoutPrinter(MazePrinter):
    # Since we have to combine these at the line level, output three strings, one for each line
    def printCell(self, cell, isStart=None, isEnd=None):
        if isStart is None:
            isStart = False
        if isEnd is None:
            isEnd = False
        openings = cell.getOpenings()
        lines = [['+', '-', '+'], ['|', ' ', '|'], ['+' ,'-', '+']]

        if MazeOpening.NORTH in openings:
            lines[0][1] = ' '
        if MazeOpening.WEST in openings:
            lines[1][0] = ' '
        if MazeOpening.EAST in openings:
            lines[1][2] = ' '
        if MazeOpening.SOUTH in openings:
            lines[2][1] = ' '

        if openings == 0:
            lines[1][1] = '#'
        if isStart:
            lines[1][1] = '*'
        if isEnd:
            lines[1][1] = '0'

        return [''.join(line) for line in lines]

    def print(self, mazeDefinition):
        (width, height) = mazeDefinition.getSize()
        cells = mazeDefinition.getCells()
        start = mazeDefinition.getStart()
        end = mazeDefinition.getEnd()

        output = []
        for y in range(height):
            cellLines = [self.printCell(cells[x][y], isStart=(start == (x,y)), isEnd=(end == (x,y))) for x in range(width)]
            output.append('\n'.join(''.join(cell[line] for cell in cellLines) for line in range(3)))

        return '\n'.join(output)

class SuccinctPrintoutPrinter(MazePrinter):
    def top(self, cell):
        if cell is not None and MazeOpening.NORTH in cell.getOpenings():
            return '+ '
        return '+-'
    def bottom(self, cell):
        if cell is not None and MazeOpening.SOUTH in cell.getOpenings():
            return '+ '
        return '+-'

    def left(self, cell):
        if cell is not None and MazeOpening.WEST in cell.getOpenings():
            return ' '
        return '|'

    def right(self, cell):
        if cell is not None and MazeOpening.EAST in cell.getOpenings():
            return ' '
        return '|'

    def center(self, cell, isStart, isEnd):
        if isStart:
            return '*'
        if isEnd:
            return '0'
        if cell.getOpenings() == 0:
            return '#'
        return ' '

    def print(self, mazeDefinition):
        (width, height) = mazeDefinition.getSize()
        cells = mazeDefinition.getCells()
        start = mazeDefinition.getStart()
        end = mazeDefinition.getEnd()

        output = ''
        for y in range(height):
            # tops first
            for x in range(width):
                cell = cells[x][y]
                output += self.top(cell)
            # cap off the tops
            output += '+\n'
            # then mids
            for x in range(width):
                cell = cells[x][y]
                isStart = (x, y) == start
                isEnd = (x, y) == end
                output += self.left(cell)
                output += self.center(cell, isStart, isEnd)
            # cap off the mids
            output += self.left(cells[0][y]) + '\n'
        for x in range(width):
            output += self.top(cells[x][0])
        output += '+'
        return output

class MazeBoxDefinitionPrinter(MazePrinter):
    PREAMBLE = '''//-------------------------------------------------------
// Import file for maze_box.scad or maze_box_inv.scad
// This file defines the maze.
//-------------------------------------------------------
// This file must define the X and Y grid sizes
// of the maze, and define a routine called
// "make_maze()".
//------------------------------------------------
//
// Vertical lines are done with linear_extrude using a circle
// Horizontal lines are done with rotate_extrude
// Spheres cap all intersections except T-intersects
//
// Requirements:
//   Maze endpoint must be put at y = 1
//   Exit must be at y = ygrid.
//   No paths other than exit higher than y = ygrid - 2
//
// Recommendations:
//   No paths other than exit higher than y = ygrid - 3
//           (otherwise the lid can be pulled off with a
//           bit of twisting)
//   No paths other than endline at y = 1 (otherwise you
//           get a false solution)
//
//---------------------------------------------------------
'''
    INDENT = 3

    ## Note for all of these functions, the OpenSCAD script expects 1-indexed positions, where our maze generation uses 0-indexed, so we always add 1 to everything (except width and height, since those are sizes rather than indices)
    def format_linecarve(self, pos0, pos1):
        if not (pos0[0] == pos1[0] or pos0[1] == pos1[1]):
            raise Exception('Lines cannot be diagonal')
        return 'maze_line(i, {x1:d}, {y1:d}, {x2:d}, {y2:d});'.format(x1=pos0[0]+1, y1=pos0[1]+1, x2=pos1[0]+1, y2=pos1[1]+1)

    ## This is the start in our maze generator parlance
    def format_endline(self, pos0, pos1):
        if pos0[1] != pos1[1]:
            raise Exception('End line has to be on the same y')
        minx = min(pos0[0], pos1[0])
        maxx = max(pos0[0], pos1[0])
        return 'maze_endline(i, {x1:d}, {x2:d}, {y:d});'.format(x1=minx+1, x2=maxx+1, y=pos0[1]+1)

    def format_intersection(self, pos):
        return 'maze_line(i, {x:d}, {y:d}, {x:d}, {y:d});'.format(x=pos[0]+1, y=pos[1]+1)

    def format_start(self, pos, width):
        x = pos[0]
        y = pos[1]
        # The position input is the maze position, which we'll then interpret to create as wide of a resting position as we can
        left = x >= width/2
        # OpenSCAD script doesn't care about going "out of bounds", so we can just arbitrarily go 3 units in any direction; you *have* guaranteed that there's nothing else on y=0, right?
        approachX = x-1 if left else x+1
        endX = approachX - 2 if left else approachX + 2
        return '\n'.join(['// Beginning (locked) position ({x:d}, {y:d})'.format(x=x+1, y=y+1),
                  ## left/right approach
                  self.format_linecarve((x, y), (approachX, y)),
                  self.format_endline((endX, y), (approachX, y)),
                  self.format_linecarve((x, y), (x, y+1)),
                  ## End detent and approach/end intersection
                  self.format_intersection((x, y)),
                  self.format_intersection((endX, y)),
                  self.format_intersection((approachX, y))])

    def format_gridsize(self, width, height):
        return '''// Maze grid size in X (units)
xgrid = {:d};

// Maze grid size in Y (units)
ygrid = {:d};
'''.format(width, height)

    def print(self, mazeDefinition):
        (width, height) = mazeDefinition.getSize()
        cells = mazeDefinition.getCells()
        start = mazeDefinition.getStart()
        end = mazeDefinition.getEnd()
        ## We initialize with the preamble, the maze overall size, and the endline (start position)
        output = '\n'.join([self.PREAMBLE,
                self.format_gridsize(width, height),
                'module make_maze(i) {\n'])
        inner = self.format_start(start, width) + '\n// Maze body'
        intersections = []
        lines = []
        # We have taken care of the beginning and the carve from the beginning to the next layer, so starting from y=1, run upward
        for iy in range(height-1):
            y = iy+1
            # only look up and right, we can go "offscreen" in positive directions but not negative
            # down is taken care of by the previous line, left is taken care of by the previous cell (or, in the case of wraparounds, the rightmost cell)
            for x in range(width):
                cell = cells[x][y]
                openings = cell.getOpenings()
                if openings == 0:
                    continue
                intersections.append(self.format_intersection((x, y)))
                if MazeOpening.EAST in openings:
                    lines.append(self.format_linecarve((x, y), (x+1, y)))
                if MazeOpening.SOUTH in openings:
                    lines.append(self.format_linecarve((x, y), (x, y+1)))
        inner += '\n// Lines\n' + '\n'.join(lines)
        inner += '\n// Intersections\n' + '\n'.join(intersections)
        output += textwrap.indent(inner, ' '*self.INDENT)
        output += '\n}'

        return output




# For use with a cylindrical projection (so x=0 may connect to x=(width-1))
class MazeBoxGenerator(MazeGenerator):
    SAFE_HEIGHT = 3 # height that must be reserved for the exit line
    
    def wraparoundX(self, x, delta, width):
        if not (delta == -1 or delta == 1):
            raise Exception('Delta must be either 1 or -1')
        if x == 0 and delta < 0:
            return width -1
        if x == width-1 and delta >0:
            return 0
        return x + delta

    def getValidMoves(self, visited, tip, width, height):
        validMoves = []
        (x, y) = tip
        left = self.wraparoundX(x, -1, width)
        right = self.wraparoundX(x, 1, width)
        if not visited[left][y]:
            validMoves.append( ((left, y), MazeOpening.WEST) )
        if not visited[right][y]:
            validMoves.append( ((right, y), MazeOpening.EAST) )
        if y > 0:
            if not visited[x][y-1]:
                validMoves.append( ((x, y-1), MazeOpening.NORTH) )
        if y < height-1:
            if not visited[x][y+1]:
                validMoves.append( ((x, y+1), MazeOpening.SOUTH) )
        return validMoves

    def generate(self, width, totalHeight, seed):
        # Constraints:
        #  * No maze elements at Y=0 apart from the start
        #  * No maze elements at Y=(height-4) apart from the end
        #  * Start must be at Y=0
        #  * End must be at Y=(height-1)
        height = totalHeight-self.SAFE_HEIGHT
        if height <= 1:
            raise Exception('Must generate a maze of height >= 5')
        if width <= 3:
            raise Exception('Must generate a maze of width >= 3')
        if seed is None:
            seed = random.randrange(1000000)
        rng = random.Random(seed)
        visited = [[False for y in range(totalHeight)] for x in range(width)]
        start = (rng.randrange(width), 0)
        end = (rng.randrange(width), totalHeight-1)
        maze = MazeDefinition(width, totalHeight, allowWrapX=True)
        maze.setStart(start[0], start[1])
        maze.setEnd(end[0], end[1])
        # seal off (pre-visit) the start level so that we don't try to visit any cell within
        for x in range(width):
            visited[x][start[1]] = True
        # seal off (pre-visit) the end levels except the end cell and the direct line below it
        for y in range(self.SAFE_HEIGHT):
            for x in range(width):
                if x == end[0]:
                    continue
                visited[x][totalHeight-(y+1)] = True
        tips = [start]
        iterations = 0
        maxIterations = width*height*5
        # While any unvisited cells exist...
        while any(not visited[x][y] for x in range(width) for y in range(totalHeight)):
            iterations+=1
            if iterations >= maxIterations:
                print('Iteration {:d} | Infinite loop detected, returning what we have; tips: {:s}\nvisited: {:s}'.format(iterations, str(tips), str(visited)))
                break
            if len(tips) == 0:
                print('Iteration {:d} | No tips exist; visited {:s}'.format(iterations, str(visited)))
                break
            tipsCopy = rng.sample(tips,  k=len(tips))
            tips = set()
            for tip in tipsCopy:
                validMoves = self.getValidMoves(visited, tip, width, totalHeight)
                if len(validMoves) == 0:
                    continue
                if len(validMoves) > 1:
                    tips.add(tip)
                chosen = rng.choice(validMoves)
                newTip = chosen[0]
                carveDirection = chosen[1]
                maze.carve(tip[0], tip[1], carveDirection)
                visited[newTip[0]][newTip[1]] = True
                tips.add(newTip)
            tips = [tip for tip in tips]
        return maze


_keyFunc = lambda clazz: clazz.__name__
_mazeGenerators = [MazeBoxGenerator]
_mazePrinters = [VerbosePrintoutPrinter, SuccinctPrintoutPrinter, MazeBoxDefinitionPrinter]
mazeGenerators = {_keyFunc(generator):generator for generator in _mazeGenerators}
mazePrinters = {_keyFunc(printer):printer for printer in _mazePrinters}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('width', type=int, help='Width of your maze')
    parser.add_argument('height', type=int, help='Height of your maze')
    parser.add_argument('seed', type=int, help='Seed for the resulting maze')
    parser.add_argument('--generator', choices=mazeGenerators.keys(), default=_keyFunc(_mazeGenerators[0]), help='Which generator to use to generate the maze')
    parser.add_argument('--printer', choices=mazePrinters.keys(), default=_keyFunc(_mazePrinters[0]), help='Which printer to use to output the maze; default is %(default)s')

    args = parser.parse_args()

    print(mazePrinters.get(args.printer)().print(mazeGenerators.get(args.generator)().generate(args.width, args.height, args.seed)))
