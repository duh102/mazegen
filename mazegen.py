#!/usr/bin/env python3
# (c) Will Morrow Dec 2024
# See LICENSE file in this repo for limitations and conditions
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

    def setOpenings(self, newOpenings):
        self._openings = newOpenings

    def block(self, blockFrom):
        if blockFrom is None or blockFrom == 0:
            raise Exception('Must block from at least one direction')
        self._openings = self._openings & (~blockFrom)

    def carve(self, openFrom):
        if openFrom is None or openFrom == 0:
            raise Exception('Must open from at least one direction')
        self._openings = self._openings | openFrom

class MazeDefinition(object):
    def __init__(self, width, height, seed, generator, params, allowWrapX=None, allowWrapY=None):
        if width is None or height is None or seed is None:
            raise Exception('Must define width, height, seed, generator, and generator params')
        self._width = width
        self._height = height
        self._seed = seed
        self._generator = generator
        self._params = params
        self._allowWrapX = False if allowWrapX is None else allowWrapX
        self._allowWrapY = False if allowWrapY is None else allowWrapY
        self._cells = [[MazeCell() for y in range(height)] for x in range(width)]
        self._start = (0, 0)
        self._end = (0, 0)

    def getSize(self):
        return (self._width, self._height)

    def getSeed(self):
        return self._seed

    def getGenerator(self):
        return self._generator

    def getParams(self):
        return self._params

    def getStart(self):
        return self._start

    def getEnd(self):
        return self._end

    def getCells(self):
        return self._cells

    def getWrapX(self):
        return self._allowWrapX

    def getWrapY(self):
        return self._allowWrapY

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

class MazeFlipper(object):
    def getNewOpenings(self, openings, flipX, flipY):
        newOpenings = MazeOpening(0)
        if flipX:
            if MazeOpening.EAST in openings:
                newOpenings = newOpenings | MazeOpening.WEST
            if MazeOpening.WEST in openings:
                newOpenings = newOpenings | MazeOpening.EAST
        else:
            if MazeOpening.EAST in openings:
                newOpenings = newOpenings | MazeOpening.EAST
            if MazeOpening.WEST in openings:
                newOpenings = newOpenings | MazeOpening.WEST
        if flipY:
            if MazeOpening.NORTH in openings:
                newOpenings = newOpenings | MazeOpening.SOUTH
            if MazeOpening.SOUTH in openings:
                newOpenings = newOpenings | MazeOpening.NORTH
        else:
            if MazeOpening.NORTH in openings:
                newOpenings = newOpenings | MazeOpening.NORTH
            if MazeOpening.SOUTH in openings:
                newOpenings = newOpenings | MazeOpening.SOUTH
        return newOpenings

    def flip(self, maze, flipX=None, flipY=None):
        if flipX is None:
            flipX = False
        if flipY is None:
            flipY = False
        if not (flipX or flipY):
            return maze
        oldCells = maze.getCells()
        (width, height) = maze.getSize()
        toRet = MazeDefinition(width, height, maze.getSeed(), maze.getGenerator(), maze.getParams(), allowWrapX=maze.getWrapX(), allowWrapY=maze.getWrapY())
        newCells = toRet.getCells()
        for x in range(width):
            for y in range(height):
                reflectX = width-1-x if flipX else x
                reflectY = height-1-y if flipY else y
                if (x, y) == maze.getStart():
                    toRet.setStart(reflectX, reflectY)
                if (x, y) == maze.getEnd():
                    toRet.setEnd(reflectX, reflectY)
                oldCell = oldCells[x][y]
                newCells[reflectX][reflectY].setOpenings(self.getNewOpenings(oldCell.getOpenings(), flipX, flipY))
        return toRet

class MazePrinter(object):
    def print(self, mazeDefinition, args):
        raise Exception('Not implemented')

class MazeGenerator(object):
    def generate(self, width, height, seed, args):
        raise Exception('Not implemented')

class PrintoutPrinter(MazePrinter):
    def getMetadataHeader(self, mazeDefinition):
        (width, height) = mazeDefinition.getSize()
        seed = mazeDefinition.getSeed()
        generator = mazeDefinition.getGenerator()
        params = mazeDefinition.getParams()

        paramsStr = '({:s})'.format(', '.join('{:s}: {:s}'.format(key, value) for (key,value) in sorted(params.items(), key=lambda p: p[0])))
        return '{w:d}x{h:d} maze ({seed})\nGenerated by {gen:s} {params:s}'.format(w=width, h=height, seed=seed, gen=generator, params='' if len(params) == 0 else paramsStr)


class VerbosePrintoutPrinter(PrintoutPrinter):
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

    def print(self, mazeDefinition, args):
        flipX = False
        flipY = False
        if 'flipX' in args.keys():
            flipX = True if args['flipX'].lower() == 'true' else False
        if 'flipY' in args.keys():
            flipY = True if args['flipY'].lower() == 'true' else False
        mazeDefinition = MazeFlipper().flip(mazeDefinition, flipX=flipX, flipY=flipY)
        (width, height) = mazeDefinition.getSize()
        cells = mazeDefinition.getCells()
        start = mazeDefinition.getStart()
        end = mazeDefinition.getEnd()

        output = []
        for y in range(height):
            cellLines = [self.printCell(cells[x][y], isStart=(start == (x,y)), isEnd=(end == (x,y))) for x in range(width)]
            output.append('\n'.join(''.join(cell[line] for cell in cellLines) for line in range(3)))

        return self.getMetadataHeader(mazeDefinition) + '\n\n' + '\n'.join(output)

class SuccinctPrintoutPrinter(PrintoutPrinter):
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

    def print(self, mazeDefinition, args):
        flipX = False
        flipY = False
        if 'flipX' in args.keys():
            flipX = True if args['flipX'].lower() == 'true' else False
        if 'flipY' in args.keys():
            flipY = True if args['flipY'].lower() == 'true' else False
        mazeDefinition = MazeFlipper().flip(mazeDefinition, flipX=flipX, flipY=flipY)
        (width, height) = mazeDefinition.getSize()
        cells = mazeDefinition.getCells()
        start = mazeDefinition.getStart()
        end = mazeDefinition.getEnd()

        output = self.getMetadataHeader(mazeDefinition) + '\n\n'
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

    def getMetadataHeader(self, mazeDefinition):
        (width, height) = mazeDefinition.getSize()
        seed = mazeDefinition.getSeed()
        generator = mazeDefinition.getGenerator()
        params = mazeDefinition.getParams()
        start = mazeDefinition.getStart()
        end = mazeDefinition.getEnd()

        paramsStr = '({:s})'.format(', '.join('{:s}: {:s}'.format(key, value) for (key,value) in sorted(params.items(), key=lambda p: p[0])))
        return '// {w:d}x{h:d} maze ({seed})\n// Generated by {gen:s} {params:s}\n//Start: ({sx:d}, {sy:d})\n//End: ({ex:d}, {ey:d})'.format(w=width,
                h=height, seed=seed, gen=generator, params='' if len(params) == 0 else paramsStr,
                sx = start[0],
                sy = start[1],
                ex = end[0],
                ey = end[1])

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

    def print(self, mazeDefinition, args):
        flipX = False
        flipY = False
        if 'flipX' in args.keys():
            flipX = True if args['flipX'].lower() == 'true' else False
        if 'flipY' in args.keys():
            flipY = True if args['flipY'].lower() == 'true' else False
        mazeDefinition = MazeFlipper().flip(mazeDefinition, flipX=flipX, flipY=flipY)
        (width, height) = mazeDefinition.getSize()
        cells = mazeDefinition.getCells()
        start = mazeDefinition.getStart()
        end = mazeDefinition.getEnd()
        ## We initialize with the preamble, the maze overall size, and the endline (start position)
        output = '\n'.join([self.PREAMBLE,
                self.getMetadataHeader(mazeDefinition),
                self.format_gridsize(width, height),
                'module make_maze(i) {\n'])
        inner = self.format_start(start, width) + '\n// Maze body'
        intersections = set()
        lines = []
        # We have taken care of the beginning and the carve from the beginning to the next layer, so starting from y=1, run upward
        # We can simplify our generated path map by only outputting carves in straight lines, either vertically or around the circumference of the cylinder
        # Each line can be continuous until it's interrupted by a wall
        # We still need to output intersections or stops, but we don't need duplicates for both x and y, so we use a set of coordinates rather than a list
        # Horizontal lines
        # (y == 0 is used for the start, skip it)
        for iy in range(height-1):
            y = iy+1
            lineStart = None
            for x in range(width):
                here = (x, y)
                cell = cells[x][y]
                openings = cell.getOpenings()
                # For horizontal lines, we may have exits to the left or right of the bounds of the maze, so we have to handle them here
                # We'll just use the x==0 case because it's easier to handle
                if x == 0 and MazeOpening.WEST in openings:
                    lineStart = (-1, y)
                if lineStart is not None: # we're currently making a line
                    if MazeOpening.EAST not in openings:
                        # We've hit an end; close this line, add it to the list of lines, and add the endpoints to the set of intersections
                        lines.append(self.format_linecarve(lineStart, here))
                        lineStart = None
                        intersections.add(here)
                else: # we're not currently making a line
                    if MazeOpening.EAST in openings:
                        # we've hit a start; start the line here
                        lineStart = here
                        intersections.add(here)
            if lineStart is not None:
                # We didn't hit an end before getting to the end of the grid; make a line ending outside the maze
                lines.append(self.format_linecarve(lineStart, (width, y)))
        # Vertical lines
        for x in range(width):
            lineStart = None
            for iy in range(height-1):
                y = iy+1
                here = (x, y)
                cell = cells[x][y]
                openings = cell.getOpenings()
                # It's not possible to have off-grid lines vertically, so we have very simple logic here
                # we start a line when there's no line and we end it when there's no opening
                if lineStart is not None: # we're currently making a line
                    # No need to check for intersections, those were already taken care of by the horizontal lines
                    if MazeOpening.SOUTH not in openings:
                        # We've hit an end; cap the current line and register an intersection
                        lines.append(self.format_linecarve(lineStart, here))
                        lineStart = None
                        intersections.add(here)
                if lineStart is None and MazeOpening.SOUTH in openings:
                    lineStart = here
                    intersections.add(here)
            if lineStart is not None:
                # We didn't hit an end before getting to the end of the grid; make a line ending outside the maze
                lines.append(self.format_linecarve(lineStart, (x, height)))
        inner += '\n// Lines (' + str(len(lines)) + ')\n' + '\n'.join(lines)
        inner += '\n// Intersections (' + str(len(intersections)) + ')\n' + '\n'.join(self.format_intersection(s) for s in intersections)
        output += textwrap.indent(inner, ' '*self.INDENT)
        output += '\n}'

        return output

class ReceiptAccessing(object):
    QUARTER_FILL = str(b'\xb0', 'ibm437')
    HALF_FILL = str(b'\xb1', 'ibm437')
    THREEQ_FILL =str(b'\xb2', 'ibm437')
    # Key: NSEW = single line in each direction
    # NNSEW = double line from N, single line from other directions
    # NNS = double line from N, single line to S, no other lines
    NS = str(b'\xb3', 'ibm437')
    NSW = str(b'\xb4', 'ibm437')
    NSWW = str(b'\xb5', 'ibm437')
    NNSSW = str(b'\xb6', 'ibm437')
    SSW = str(b'\xb7', 'ibm437')
    SWW = str(b'\xb8', 'ibm437')
    NNSSWW = str(b'\xb9', 'ibm437')
    NNSS = str(b'\xba', 'ibm437')
    SSWW = str(b'\xbb', 'ibm437')
    NNWW = str(b'\xbc', 'ibm437')
    NNW = str(b'\xbd', 'ibm437')
    NWW = str(b'\xbe', 'ibm437')
    SW = str(b'\xbf', 'ibm437')
    NE = str(b'\xc0', 'ibm437')
    NEW = str(b'\xc1', 'ibm437')
    SEW = str(b'\xc2', 'ibm437')
    NSE = str(b'\xc3', 'ibm437')
    EW = str(b'\xc4', 'ibm437')
    NSEW = str(b'\xc5', 'ibm437')
    NSEE = str(b'\xc6', 'ibm437')
    NNSSE = str(b'\xc7', 'ibm437')
    NNEE = str(b'\xc8', 'ibm437')
    SSEE = str(b'\xc9', 'ibm437')
    NNEEWW = str(b'\xca', 'ibm437')
    SSEEWW = str(b'\xcb', 'ibm437')
    NNSSEE = str(b'\xcc', 'ibm437')
    EEWW = str(b'\xcd', 'ibm437')
    NNSSEEWW = str(b'\xce', 'ibm437')
    NEEWW = str(b'\xcf', 'ibm437')
    NNEW = str(b'\xd0', 'ibm437')
    SEEWW = str(b'\xd1', 'ibm437')
    SSEW = str(b'\xd2', 'ibm437')
    NNE = str(b'\xd3', 'ibm437')
    NEE = str(b'\xd4', 'ibm437')
    SEE = str(b'\xd5', 'ibm437')
    SSE = str(b'\xd6', 'ibm437')
    NNSSEW = str(b'\xd7', 'ibm437')
    NSEEWW = str(b'\xd8', 'ibm437')
    NW = str(b'\xd9', 'ibm437')
    SE = str(b'\xda', 'ibm437')
    FULL_BLOCK = str(b'\xdb', 'ibm437')
    HALF_HB_BLOCK = str(b'\xdc', 'ibm437')
    HALF_VL_BLOCK = str(b'\xdd', 'ibm437')
    HALF_VR_BLOCK = str(b'\xde', 'ibm437')
    HALF_HT = str(b'\xdf', 'ibm437')

class ReceiptMazePrinter(MazePrinter, ReceiptAccessing):
    DOUBLE_BAR_MAP = {
        MazeOpening(0) : ' ',
        MazeOpening.NORTH: ReceiptAccessing.NNEW,
        MazeOpening.SOUTH: ReceiptAccessing.SSEW,
        MazeOpening.EAST: ReceiptAccessing.NSEE,
        MazeOpening.WEST: ReceiptAccessing.NSWW,
        MazeOpening.NORTH | MazeOpening.SOUTH: ReceiptAccessing.NNSS,
        MazeOpening.NORTH | MazeOpening.EAST: ReceiptAccessing.NNEE,
        MazeOpening.NORTH | MazeOpening.WEST: ReceiptAccessing.NNWW,
        MazeOpening.SOUTH | MazeOpening.EAST: ReceiptAccessing.SSEE,
        MazeOpening.SOUTH | MazeOpening.WEST: ReceiptAccessing.SSWW,
        MazeOpening.EAST | MazeOpening.WEST: ReceiptAccessing.EEWW,
        MazeOpening.NORTH | MazeOpening.SOUTH | MazeOpening.EAST: ReceiptAccessing.NNSSEE,
        MazeOpening.NORTH | MazeOpening.SOUTH | MazeOpening.WEST: ReceiptAccessing.NNSSWW,
        MazeOpening.NORTH | MazeOpening.EAST | MazeOpening.WEST: ReceiptAccessing.NNEEWW,
        MazeOpening.SOUTH | MazeOpening.EAST | MazeOpening.WEST: ReceiptAccessing.SSEEWW,
        MazeOpening.NORTH | MazeOpening.SOUTH | MazeOpening.EAST | MazeOpening.WEST: ReceiptAccessing.NNSSEEWW
    }
    def getMetadataHeader(self, mazeDefinition):
        (width, height) = mazeDefinition.getSize()
        seed = mazeDefinition.getSeed()
        generator = mazeDefinition.getGenerator()
        params = mazeDefinition.getParams()

        paramsStr = '({:s})'.format(', '.join('{:s}: {:s}'.format(key, value) for (key,value) in sorted(params.items(), key=lambda p: p[0])))
        return '{w:d}x{h:d} maze ({seed})\nGenerated by {gen:s} {params:s}'.format(w=width, h=height, seed=seed, gen=generator, params='' if len(params) == 0 else paramsStr)

    def cell_to_char(self, cell):
        openings = cell.getOpenings()
        return self.DOUBLE_BAR_MAP.get(openings, self.FULL_BLOCK)

    def print(self, mazeDefinition, args):
        try:
            import ncr7197
        except Exception as e:
            raise Exception('Unable to import the printer, failing', e)
        from ncr7197 import NCR7197, PRINT_CUT_OFFSET, MAX_WIDTH
        max_maze_width = MAX_WIDTH
        (width, height) = mazeDefinition.getSize()
        if width > max_maze_width:
            raise Exception('Maximum maze width is {:d}'.format(max_maze_width))
        printer = NCR7197('/dev/ttyUSB0') # going to have to make some parameters to make this work properly
        flipX = False
        flipY = False
        if 'flipX' in args.keys():
            flipX = True if args['flipX'].lower() == 'true' else False
        if 'flipY' in args.keys():
            flipY = True if args['flipY'].lower() == 'true' else False
        mazeDefinition = MazeFlipper().flip(mazeDefinition, flipX=flipX, flipY=flipY)
        cells = mazeDefinition.getCells()
        start = mazeDefinition.getStart()
        end = mazeDefinition.getEnd()

        output = self.getMetadataHeader(mazeDefinition)+'\n\n'
        for y in range(height):
            line = ''
            for x in range(width):
                if (x, y) == start or (x, y) == end:
                    line += '@' if (x, y) == start else 'X'
                else:
                    line += self.cell_to_char(cells[width-1-x][y])
            output += line + '\n'
        printer.print(output + '\n'*PRINT_CUT_OFFSET)
        printer.cut()
        return ''

class DrawableReceiptMazePrinter(MazePrinter, ReceiptAccessing):
    SINGLE_BAR_MAP = {
        MazeOpening(0) : ' ',
        MazeOpening.NORTH: ReceiptAccessing.NS,
        MazeOpening.SOUTH: ReceiptAccessing.NS,
        MazeOpening.EAST: ReceiptAccessing.EW,
        MazeOpening.WEST: ReceiptAccessing.EW,
        MazeOpening.NORTH | MazeOpening.SOUTH: ReceiptAccessing.NS,
        MazeOpening.NORTH | MazeOpening.EAST: ReceiptAccessing.NE,
        MazeOpening.NORTH | MazeOpening.WEST: ReceiptAccessing.NW,
        MazeOpening.SOUTH | MazeOpening.EAST: ReceiptAccessing.SE,
        MazeOpening.SOUTH | MazeOpening.WEST: ReceiptAccessing.SW,
        MazeOpening.EAST | MazeOpening.WEST: ReceiptAccessing.EW,
        MazeOpening.NORTH | MazeOpening.SOUTH | MazeOpening.EAST: ReceiptAccessing.NSE,
        MazeOpening.NORTH | MazeOpening.SOUTH | MazeOpening.WEST: ReceiptAccessing.NSW,
        MazeOpening.NORTH | MazeOpening.EAST | MazeOpening.WEST: ReceiptAccessing.NEW,
        MazeOpening.SOUTH | MazeOpening.EAST | MazeOpening.WEST: ReceiptAccessing.SEW,
        MazeOpening.NORTH | MazeOpening.SOUTH | MazeOpening.EAST | MazeOpening.WEST: ReceiptAccessing.NSEW
    }

    def getWallConnections(self, x, y, field):
        return ((MazeOpening.NORTH if field[x][y-1] != ' ' else MazeOpening(0))
                | (MazeOpening.SOUTH if field[x][y+1] != ' ' else MazeOpening(0))
                | (MazeOpening.EAST if field[x+1][y] != ' ' else MazeOpening(0))
                | (MazeOpening.WEST if field[x-1][y] != ' ' else MazeOpening(0)))

    def getMetadataHeader(self, mazeDefinition):
        (width, height) = mazeDefinition.getSize()
        seed = mazeDefinition.getSeed()
        generator = mazeDefinition.getGenerator()
        params = mazeDefinition.getParams()

        paramsStr = '({:s})'.format(', '.join('{:s}: {:s}'.format(key, value) for (key,value) in sorted(params.items(), key=lambda p: p[0])))
        return '{w:d}x{h:d} maze ({seed})\nGenerated by {gen:s} {params:s}'.format(w=width, h=height, seed=seed, gen=generator, params='' if len(params) == 0 else paramsStr)

    def print(self, mazeDefinition, args):
        try:
            import ncr7197
        except Exception as e:
            raise Exception('Unable to import the printer, failing', e)
        from ncr7197 import NCR7197, PRINT_CUT_OFFSET, MAX_WIDTH
        max_maze_width = int(MAX_WIDTH/2)-1
        (width, height) = mazeDefinition.getSize()
        if width > max_maze_width:
            raise Exception('Maximum maze width is {:d}'.format(max_maze_width))
        printer = NCR7197('/dev/ttyUSB0') # going to have to make some parameters to make this work properly
        flipX = False
        flipY = False
        if 'flipX' in args.keys():
            flipX = True if args['flipX'].lower() == 'true' else False
        if 'flipY' in args.keys():
            flipY = True if args['flipY'].lower() == 'true' else False
        mazeDefinition = MazeFlipper().flip(mazeDefinition, flipX=flipX, flipY=flipY)
        cells = mazeDefinition.getCells()
        start = mazeDefinition.getStart()
        end = mazeDefinition.getEnd()

        field_transform = lambda v: v*2+1
        field_width = field_transform(width)
        field_height = field_transform(height)
        field = [[self.HALF_FILL for y in range(field_height)] for x in range(field_width)]
        # Fill in the top and bottom edges, as well as all the intermediate walls except the crosses
        for x in range(field_width):
            if x == 0:
                field[x][0] = self.SSEE
                field[x][field_height-1] = self.NNEE
                continue
            if x == field_width-1:
                field[x][0] = self.SSWW
                field[x][field_height-1] = self.NNWW
                continue
            field[x][0] = self.EEWW
            field[x][field_height-1] = self.EEWW
            if x % 2 == 1:
                for y in range(2, field_height-1, 2):
                    field[x][y] = self.EW
            else:
                for y in range(1, field_height, 2):
                    field[x][y] = self.NS
        
        # Fill in the left and right edges; intermediates were taken care of already
        for y in range(field_height):
            if y == 0 or y == field_height-1:
                continue
            field[0][y] = self.NNSS
            field[field_width-1][y] = self.NNSS
        for y in range(height):
            fy = field_transform(y)
            for x in range(width):
                loc = (x,y)
                fx = field_transform(x)
                cell = cells[x][y]
                openings = cell.getOpenings()
                # handle center
                if start == loc:
                    field[fx][fy] = '@'
                elif end == loc:
                    field[fx][fy] = 'X'
                else:
                    if openings == MazeOpening(0):
                        field[fx][fy] = self.HALF_FILL
                    else:
                        field[fx][fy] = ' '
                # handle top
                if MazeOpening.NORTH in openings:
                    field[fx][fy-1] = ' '
                if MazeOpening.SOUTH in openings:
                    field[fx][fy+1] = ' '
                if MazeOpening.EAST in openings:
                    field[fx+1][fy] = ' '
                if MazeOpening.WEST in openings:
                    field[fx-1][fy] = ' '

        # Now that all the cardinal direction walls are set, we'll do all the crossings
        for x in range(2, field_width-1, 2):
            if field[x][1] != ' ':
                field[x][0] = self.SEEWW
            if field[x][field_height-2] != ' ':
                field[x][field_height-1] = self.NEEWW
            for y in range(2, field_height-1, 2):
                directions = self.getWallConnections(x, y, field)
                field[x][y] = self.SINGLE_BAR_MAP.get(directions, '!')
        for y in range(2, field_height-1, 2):
            if field[1][y] != ' ':
                field[0][y] = self.NNSSE
            if field[field_width-2][y] != ' ':
                field[field_width-1][y] = self.NNSSW

        printer.print(self.getMetadataHeader(mazeDefinition)+'\n\n' + '\n'.join([''.join([field[x][y] for x in range(field_width)]) for y in range(field_height)]) + '\n'*PRINT_CUT_OFFSET)
        printer.cut()
        return 'printed'

class RandomTipCarverMazeBuilder(object):
    def wraparoundX(self, x, delta, width):
        if not (delta == -1 or delta == 1):
            raise Exception('Delta must be either 1 or -1')
        if x == 0 and delta < 0:
            return width -1
        if x == width-1 and delta >0:
            return 0
        return x + delta

    def getValidMoves(self, visited, tip, width, height, wrapXAllowed):
        validMoves = []
        (x, y) = tip
        if wrapXAllowed:
            left = self.wraparoundX(x, -1, width)
            right = self.wraparoundX(x, 1, width)
            if not visited[left][y]:
                validMoves.append( ((left, y), MazeOpening.WEST) )
            if not visited[right][y]:
                validMoves.append( ((right, y), MazeOpening.EAST) )
        else:
            if x > 0 and not visited[x-1][y]:
                validMoves.append( ((x-1, y), MazeOpening.WEST) )
            if x < width-1 and not visited[x+1][y]:
                validMoves.append( ((x+1, y), MazeOpening.EAST) )
        if y > 0 and not visited[x][y-1]:
            validMoves.append( ((x, y-1), MazeOpening.NORTH) )
        if y < height-1 and not visited[x][y+1]:
            validMoves.append( ((x, y+1), MazeOpening.SOUTH) )
        return validMoves

    def generate(self, maze, visited=None, rng=None, wrapXAllowed=None):
        (width, height) = maze.getSize()
        start = maze.getStart()
        end = maze.getEnd()
        seed = maze.getSeed()
        if rng is None:
            rng = random.Random(seed)
        if visited is None:
            visited = [[False for y in range(height)] for x in range(width)]
        if wrapXAllowed is None:
            wrapXAllowed = False
        init = (rng.randrange(width), rng.randrange(height))
        while visited[init[0]][init[1]]:
            init = (rng.randrange(width), rng.randrange(height))
        tips = [init]
        iterations = 0
        maxIterations = width*height*5
        # While any unvisited cells exist...
        while any(not visited[x][y] for x in range(width) for y in range(height)) and len(tips) > 0:
            iterations+=1
            if iterations >= maxIterations:
                print('Iteration {:d} | Infinite loop detected, returning what we have; tips: {:s}\nvisited: {:s}'.format(iterations, str(tips), str(visited)))
                break
            if len(tips) == 0:
                print('Iteration {:d} | No tips exist; visited {:s}'.format(iterations, str(visited)))
                break
            tip = rng.choice(tips)
            tips.remove(tip)
            validMoves = self.getValidMoves(visited, tip, width, height, wrapXAllowed)
            if len(validMoves) == 0:
                continue
            if len(validMoves) > 1:
                tips.insert(0, tip)
            chosen = rng.choice(validMoves)
            newTip = chosen[0]
            carveDirection = chosen[1]
            maze.carve(tip[0], tip[1], carveDirection)
            visited[newTip[0]][newTip[1]] = True
            # Ensure the end is always a single-entrance cell
            if newTip != end:
                tips.append(newTip)
        return maze

# For use with a cylindrical projection (so x=0 may connect to x=(width-1))
class MazeBoxGenerator(MazeGenerator):
    SAFE_HEIGHT = 3 # height that must be reserved for the exit line    

    def generate(self, width, totalHeight, seed, args):
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
        start = (rng.randrange(width), 0)
        end = (rng.randrange(width), totalHeight-1)
        maze = MazeDefinition(width, totalHeight, seed, self.__class__.__name__, {}, allowWrapX=True)
        maze.setStart(start[0], start[1])
        maze.setEnd(end[0], end[1])
        visited = [[False for y in range(totalHeight)] for x in range(width)]
        # seal off (pre-visit) the start level so that we don't try to visit any cell within
        for x in range(width):
            if x == start[0]:
                continue
            visited[x][start[1]] = True
        # seal off (pre-visit) the end levels except the end cell and the direct line below it
        for y in range(self.SAFE_HEIGHT):
            for x in range(width):
                if x == end[0]:
                    continue
                visited[x][totalHeight-(y+1)] = True
        return RandomTipCarverMazeBuilder().generate(maze, visited=visited, rng=rng, wrapXAllowed=True)

class GeneralMazeCarverGenerator(MazeGenerator):
    def generate(self, width, height, seed, args):
        if height <= 1:
            raise Exception('Must generate a maze of height >= 1')
        if width <= 1:
            raise Exception('Must generate a maze of width >= 1')
        if seed is None:
            seed = random.randrange(1000000)
        rng = random.Random(seed)
        start = (rng.randrange(width), rng.randrange(height))
        end = start
        while start == end:
            end = (rng.randrange(width), rng.randrange(height))
        maze = MazeDefinition(width, height, seed, self.__class__.__name__, {}, allowWrapX=True)
        maze.setStart(start[0], start[1])
        maze.setEnd(end[0], end[1])
        return RandomTipCarverMazeBuilder().generate(maze, rng=rng)

_keyFunc = lambda clazz: clazz.__name__
_mazeGenerators = [GeneralMazeCarverGenerator, MazeBoxGenerator]
_mazePrinters = [VerbosePrintoutPrinter, SuccinctPrintoutPrinter, MazeBoxDefinitionPrinter, ReceiptMazePrinter, DrawableReceiptMazePrinter]
mazeGenerators = {_keyFunc(generator):generator for generator in _mazeGenerators}
mazePrinters = {_keyFunc(printer):printer for printer in _mazePrinters}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('width', type=int, help='Width of your maze')
    parser.add_argument('height', type=int, help='Height of your maze')
    parser.add_argument('seed', type=int, help='Seed for the resulting maze')
    parser.add_argument('--generator', choices=mazeGenerators.keys(), default=_keyFunc(_mazeGenerators[0]), help='Which generator to use to generate the maze')
    parser.add_argument('--printer', choices=mazePrinters.keys(), default=_keyFunc(_mazePrinters[0]), help='Which printer to use to output the maze; default is %(default)s')
    parser.add_argument('--gen-arg', action='append', help='Add extra options in name:value format to the generator command')
    parser.add_argument('--print-arg', action='append', help='Add extra options in name:value format to the print command')

    args = parser.parse_args()

    genargs = {arg[0:arg.index(':')]:arg[arg.index(':')+1:] for arg in args.gen_arg} if args.gen_arg is not None else {}
    printargs = {arg[0:arg.index(':')]:arg[arg.index(':')+1:] for arg in args.print_arg} if args.print_arg is not None else {}

    print(mazePrinters.get(args.printer)().print(mazeGenerators.get(args.generator)().generate(args.width, args.height, args.seed, genargs), printargs))
