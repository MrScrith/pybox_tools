import struct
import sys
import getopt


def main(argv):
    inputFile = ''
    binaryFile = ''
    ifile = None
    bfile = None

    helpMessage = "assemler.py - i <assemblyFileName> -o <binaryFileName>"

    try:
        options, args = getopt.getopt(argv, "hi:o:", ["asmfile=", "binfile="])
    except getopt.GetoptError:
        print(helpMessage)
        sys.exit(2)

    for opt, arg in options:
        if opt == '-h':
            print(helpMessage)
        elif opt in ("-i", "--asmfile"):
            inputFile = arg
        elif opt in ("-o", "--binfile"):
            binaryFile = arg

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
    nextVariable = 0
    progStrings = []
    labelList = {}
    variableList = {}

    SKIP_FOR_SET = "SKIPFORSET"

    # Preprocess the lines in the assembly file to clean things up.
    for line in asmFile:

        if line[0] == '#':
            # Comment line, go to next loop
            continue

        if line[0] == '@':
            # Variable (stack) value
            vname = line.partition('@')[2]
            if vname not in variableList.keys():
                variableList[vname] = nextVariable
                nextVariable += 1
            line = line.partition('@')[0] + '@' + variableList[vname]

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

        comm = parsed_com[0][0:3]

        if   comm == "CPY":
            data = 0x0001 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "ST0":
            data = 0x0000 | parse_dest(parsed_com[1])
        elif comm == "ST1":
            data = 0x1001 | parse_dest(parsed_com[1])
        elif comm == "STN":
            data = 0x1000 | parse_dest(parsed_com[1])
        elif comm == "INC":
            data = 0x2001 | parse_signed(parsed_com[0]) | parse_source(parsed_com[1])
        elif comm == "DEC":
            data = 0x2000 | parse_signed(parsed_com[0]) | parse_source(parsed_com[1])
        elif comm == "ADD":
            data = 0x3001 | parse_signed(parsed_com[0]) | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "SUB":
            data = 0x3000 | parse_signed(parsed_com[0]) | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "MUL":
            data = 0x4001 | parse_signed(parsed_com[0]) | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "DIV":
            data = 0x4000 | parse_signed(parsed_com[0]) | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "AND":
            data = 0x5001 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "ORR":
            data = 0x5000 | parse_source(parsed_com[1]) | parse_dest(parsed_com[2])
        elif comm == "NOT":
            data = 0x6001 | parse_source(parsed_com[1])
        elif comm == "NEG":
            data = 0x6000 | parse_source(parsed_com[1])
        elif comm == "BSL":
            data = 0x7001 | parse_source(parsed_com[1])
        elif comm == "BSR":
            data = 0x7000 | parse_source(parsed_com[1])
        elif comm == "SET":
            data = 0x8000 | parse_dest(parsed_com[1])
            hasLitValue = True
            val = parsed_com[2]
            if val[0] == '@':
                # variable value...
                # TODO figure out how to handle variables
                pass
            elif val[0] == '(':
                # value is label
                litData = labelList[val[1:-1]]
            else:
                # the int function is smart enough to parse both hex and decimal, if it sees a '0x' prefix it
                # assumes hex, otherwise decimal.
                litData = int(val,0)

        elif comm == "FNC":
            data = 0x9001
        elif comm == "FNR":
            data = 0x9000

        if parsed_com[-1] == "NOJ":
            pass
        elif parsed_com[-1] == "JGZ":
            data = data | 0x0002
        elif parsed_com[-1] == "JEZ":
            data = data | 0x0004
        elif parsed_com[-1] == "JGE":
            data = data | 0x0006
        elif parsed_com[-1] == "JLZ":
            data = data | 0x0008
        elif parsed_com[-1] == "JLE":
            data = data | 0x000A
        elif parsed_com[-1] == "JNZ":
            data = data | 0x000C
        elif parsed_com[-1] == "JMP":
            data = data | 0x000E

        if binFile:
            binFile.write(struct.pack('H', data))

            if ( hasLitValue ):
                binFile.write(struct.pack('H', litData))



def  parse_signed(comm):

    retVal = 0x0000

    # If there is a signed designation on it
    if len(comm) == 4:
        # If the designation is "S" ("U" would be ignored/redundant)
        if comm[3] == 'S':
            retVal = 0x0010

    return retVal

def parse_source(source):

    rval = 0x0000

    if source == "RJP":
        pass
    elif source == "RMA":
        rval = 0x0100
    elif source == "RMD":
        rval = 0x0200
    elif source == "RG1":
        rval = 0x0300
    elif source == "RG2":
        rval = 0x0400
    elif source == "RG3":
        rval = 0x0500
    elif source == "RG4":
        rval = 0x0600
    elif source == "RG5":
        rval = 0x0700
    elif source == "RIS":
        rval = 0x0800
    elif source == "RPC":
        rval = 0x0900
    elif source == "RST":
        rval = 0x0A00
    elif source == "RAL":
        rval = 0x0B00

    return rval

def parse_dest(dest):

    rval = 0x0000

    if dest == "RJP":
        pass
    elif dest == "RMA":
        rval = 0x0020
    elif dest == "RMD":
        rval = 0x0040
    elif dest == "RG1":
        rval = 0x0060
    elif dest == "RG2":
        rval = 0x0080
    elif dest == "RG3":
        rval = 0x00A0
    elif dest == "RG4":
        rval = 0x00C0
    elif dest == "RG5":
        rval = 0x00E0

    return rval

if __name__ == "__main__":
    main(sys.argv[1:])