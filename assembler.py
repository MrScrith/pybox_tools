import struct
import sys
import getopt


def main(argv):
    inputFile = ''
    binaryFile = ''
    ifile = None
    bfile = None
    userApp = True

    helpMessage = "assemler.py -i <assemblyFileName> -b <binaryFileName> -o"

    try:
        options, args = getopt.getopt(argv, "hi:b:o", ["asmfile=", "binfile="])
    except getopt.GetoptError:
        print(helpMessage)
        sys.exit(2)

    for opt, arg in options:
        if opt == '-h':
            print(helpMessage)
        elif opt in ("-i", "--asmfile"):
            inputFile = arg
        elif opt in ("-b", "--binfile"):
            binaryFile = arg
        elif opt in '-o':
            userApp = False

    if inputFile == '':
        print(helpMessage)
        sys.exit(2)
    else:
        if binaryFile == '':
            if '.' not in inputFile:
                binaryFile = ("%s.dat" % inputFile)
            else:
                binaryFile = ("%s.dat" % inputFile.partition('.')[0])

    try:
        ifile = open(inputFile)
        bfile = open(binaryFile, "wb")

    except:
        print("Issue opening input and output files")
        sys.exit(2)

    print("input and output opened, about to parse assembly.")
    parseAsm(ifile, bfile)
    print("Parser finished, closing up.")

    ifile.close()
    bfile.flush()
    bfile.close()


def parseAsm(asmFile, binFile):
    nextVariable = 1        # Index of variable from Stack, starts at 1 (stack 0 is end of var list)
    progStrings = []        # List of program strings
    labelList = {}          # List of labels for jump instructions
    functionList = {0:{}}   # List of function variables
    curFunc = 0             # Current function index

    SKIP_FOR_SET = "SKIPFORSET"

    # Preprocess the lines in the assembly file to clean things up.
    for line in asmFile:

        if line[0] == '#':
            # Comment line, go to next loop
            continue

        if line[0] == '@':
            # Variable (stack) value

            # extract the variable name (include the @), strip off spaces.
            vname = line.partition('=')[0].strip()

            # check to see if the name exists in the current function list
            if vname not in functionList[curFunc].keys():
                # Name does not exist, so add it to the list
                functionList[curFunc][vname] = (nextVariable, line.partition('=')[2].strip())
                nextVariable += 1
            line = line.partition('@')[0] + '@' + functionList[curFunc][vname]

        if '#' in line:
            # Comment exists within the line
            # Grab the portion before the comment
            line = line.partition('#')[0]

        line = line.strip('\n\r')

        if len(line) == 0:
            continue

        if line[0] == '(' and line[-1] == ')':
            # Labels aren't add to the line, but their location is recorded, however
            # the location ends up being the next instruction, not the previous.
            labelList[line.upper()[1:-1]] = len(progStrings)
        elif len(line) > 0:
            # labels aren't added to the strings
            progStrings.append(line)
            # If it is a "set" operation it has two lines
            if line.upper()[0:3] == "SET":
                progStrings.append(SKIP_FOR_SET)

        if line[0:3] == "FNC":
            curFunc += 1
            nextVariable = 0

    # Now that it's been pre-processed, now we start putting it all together.
    for line in progStrings:

        hasLitValue = False
        data = 0x0000
        litData = 0x0000

        if line == SKIP_FOR_SET:
            # Skip, just used for aligning labels to consider set operations which
            # take two 'words' (two 16bit values)
            continue

        parsed_com = line.upper().split(':')

        comm = parsed_com[0]

        if   comm == "COPY":
            data = 0x0000 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "SET0":
            data = 0x0800 | parse_dest(parsed_com[1])
        elif comm == "SET1":
            data = 0x1000 | parse_dest(parsed_com[1])
        elif comm == "SETN":
            data = 0x1800 | parse_dest(parsed_com[1])
        elif comm == "UINC" or comm == "INC":
            data = 0x2000 | parse_source(parsed_com[1])
        elif comm == "SINC":
            data = 0x2800 | parse_source(parsed_com[1])
        elif comm == "UDEC" or comm == "DEC":
            data = 0x3000 | parse_source(parsed_com[1])
        elif comm == "SDEC":
            data = 0x3800 | parse_source(parsed_com[1])
        elif comm == "UADD" or comm == "ADD":
            data = 0x4000 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "SADD":
            data = 0x4800 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "USUB" or comm == "SUB":
            data = 0x5000 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "SSUB":
            data = 0x5800 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "UMUL" or comm == "MUL":
            data = 0x6000 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "SMUL":
            data = 0x6800 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "UDIV" or comm == "DIV":
            data = 0x7000 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "SDIV":
            data = 0x7800 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "AND":
            data = 0x8000 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "OR":
            data = 0x8800 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "NOT":
            data = 0x9000 | parse_source(parsed_com[1])
        elif comm == "NEG":
            data = 0x9800 | parse_source(parsed_com[1])
        elif comm == "BSL":
            data = 0xA000 | parse_source(parsed_com[1])
        elif comm == "BSR":
            data = 0xA800 | parse_source(parsed_com[1])
        elif comm == "SET":
            data = 0xB000 | parse_dest(parsed_com[1])
            hasLitValue = True
            val = parsed_com[2]
            if val[0] == '@':
                # variable value...
                # TODO figure out how to handle variables

                # Check list of variables
                #
                pass
            elif val[0] == '(':
                # value is label
                litData = labelList[val[1:-1]]
            else:
                # the int function is smart enough to parse both hex and decimal, if it sees a '0x' prefix it
                # assumes hex, otherwise decimal.
                litData = int(val,0)

        elif comm == "FNC":
            data = 0xB800
        elif comm == "FNR":
            data = 0xC000

        if parsed_com[-1] == "NOJ":
            pass
        elif parsed_com[-1] == "JGZ":
            data = data | 0x0200
        elif parsed_com[-1] == "JEZ":
            data = data | 0x0400
        elif parsed_com[-1] == "JGE":
            data = data | 0x0600
        elif parsed_com[-1] == "JLZ":
            data = data | 0x0800
        elif parsed_com[-1] == "JLE":
            data = data | 0x0A00
        elif parsed_com[-1] == "JNZ":
            data = data | 0x0C00
        elif parsed_com[-1] == "JMP":
            data = data | 0x0E00

        if binFile:
            binFile.write(struct.pack('H', data))

            if ( hasLitValue ):
                binFile.write(struct.pack('H', litData))


def parse_source(source):

    rval = 0x0000

    if source == "RJP":
        pass
    elif source == "RMA":
        rval = 0x0010
    elif source == "RMD":
        rval = 0x0020
    elif source == "GP1":
        rval = 0x0030
    elif source == "GP2":
        rval = 0x0040
    elif source == "GP3":
        rval = 0x0050
    elif source == "GP4":
        rval = 0x0060
    elif source == "GP5":
        rval = 0x0070
    elif source == "GP6":
        rval = 0x0080
    elif source == "GP7":
        rval = 0x0090
    elif source == "GP8":
        rval = 0x00A0
    elif source == "RIS":
        rval = 0x00B0
    elif source == "RPC":
        rval = 0x00C0
    elif source == "STK":
        rval = 0x00D0
    elif source == "ALU":
        rval = 0x00E0
    elif source == "RFL":
        rval = 0x0F0

    return rval

def parse_dest(dest):

    rval = 0x0000

    if dest == "RJP":
        pass
    elif dest == "RMA":
        rval = 0x0001
    elif dest == "RMD":
        rval = 0x0002
    elif dest == "GP1":
        rval = 0x0003
    elif dest == "GP2":
        rval = 0x0004
    elif dest == "GP3":
        rval = 0x0005
    elif dest == "GP4":
        rval = 0x0006
    elif dest == "GP5":
        rval = 0x0008
    elif dest == "GP6":
        rval = 0x0009
    elif dest == "GP7":
        rval = 0x000A
    elif dest == "GP8":
        rval = 0x000B

    return rval

if __name__ == "__main__":
    main(sys.argv[1:])