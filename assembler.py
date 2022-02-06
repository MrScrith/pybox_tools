import struct
import sys
import getopt

class programBase:
    FunctionList = None
    __userProg = False
    __curFunction = None
    __rootFunction = None


    def __init__(self, userProg):
        self.FunctionList = list()
        self.FunctionList.clear()
        self.__userProg = userProg

        self.__rootFunction = functionBase("root")
        self.__curFunction = self.__rootFunction
        self.FunctionList.append(self.__rootFunction)

    def processLine(self, line):
        breakdown = line.upper().split(':')
        if breakdown[0][0] == '!':
            self.__addFunction(line)
        elif breakdown[0] == "FNR":
            self.__closeFunction()
        elif breakdown[0][1] == '@':
            self.__addVariable(breakdown[0][2:], breakdown[1], True)
        elif breakdown[0][0] == '@':
            self.__addVariable(breakdown[0][1:], breakdown[1], False)
        elif breakdown[0][0] == '(':
            self.__addLabel(breakdown[0][1:-1])

    def __addFunction(self,funcName):
        self.__curFunction = functionBase(funcName)

    def __closeFunction(self):
        self.__curFunction = self.__rootFunction

    def __addVariable(self, name, value, globalVariable):
        if globalVariable:
            self.__rootFunction.addVariable(name, value)
        else:
            self.__curFunction.addVariable(name, value)

    def __getVariable(self, name):
        pass

    def __addInstruction(self, instruction):
        self.__curFunction.addInstruction(instruction)

    def __addLabel(self, name):
        self.__curFunction.addLabel(name)


class functionBase:
    functionAddressBase = 0x0000
    labelList = list()
    variableList = list()
    instructionList = list()
    functionName = ""
    bytecodeList = None
    SINGLE_INPUT_INSTRUCTION = ("INC", "UINC", "SINC", "DEC", "UDEC", "SDEK" ) # TODO: Fill out full single input list
    DUAL_INPUT_INSTRUCTION = ("ADD", "UADD", "SADD", "SUB", "USUB", "SSUB")    # TODO: Fill out full dual input list
    REGISTER_LIST = ("GP1", "GP2", "GP3", "GP4", "GP5", "GP6", "GP7", "GP8")   # TODO: Fill out full register list

    def __init__(self, funName):
        self.functionAddressBase = 0x0000
        self.labelList = list()
        self.labelList.clear()
        self.variableList = list()
        self.variableList.clear()
        self.instructionList = list()
        self.instructionList.clear()
        self.functionName = funName
        self.bytecodeList = bytearray()

    def addVariable(self, name, value):
        varIndex = -1
        # Add a variable to the list, if variable already exists then return -1
        if self.getVariableIndex(name) == -1:
            varIndex = len(self.variableList) + 1
            self.variableList.append((varIndex, name, value))
        return varIndex

    def getVariableIndex(self, name):
        retVal = -1
        for var in self.variableList:
            if var[1] == name:
                retVal = var[0]
        return retVal

    def addInstruction(self, instruction):

        ins = instruction.upper().split(':')
        insLen = 0

        if ins[0] in self.SINGLE_INPUT_INSTRUCTION:
            # analyze for 1 input
            pass
        elif ins[0] in self.DUAL_INPUT_INSTRUCTION:
            # analyze for 2 input
            pass
        elif ins[0] == "SET":
            # analyze for SET instruction
            if ins[1][1] == "@":
                # Local variable
                lvIndex = self.getVariableIndex(ins[1])
                if lvIndex == 1:
                    insLen += 2
                    # inc stack
                    # copy alu out to mem address
                else:
                    insLen += 3
                    # set gp8 to literal
                    # add gp8 to stack var
                    # copy alu out to mem address

            elif ins[1] in self.REGISTER_LIST:
                # Register
                insLen += 1



        self.instructionList.append(instruction)

    def addLabel(self, name):
        # Add a label at the current instruction index
        insIndex = len(self.instructionList)

        # Add the label name with the instruction index
        self.labelList.append((name, insIndex))

def main(argv):
    inputFile = ''
    binaryFile = ''
    ifile = None
    bfile = None
    userApp = True
    baseOffset = 0x0000

    helpMessage = """
    assemler.py -i <assemblyFileName> [-b <binaryFileName> -s -o <offset>]
    
    -i / --asmfile : Input assembly file to be parsed.
    -b / --binfile : Binary output file to be written. (optional)
    -s             : User/OS program, if set then program will be compiled as a system/os program, otherwise a user program.
    -o / --offset  : Address offset to place the start of the program, used to calculate jumps.
    """

    try:
        options, args = getopt.getopt(argv, "hi:b:o:u", ["asmfile=", "binfile=", "offset="])
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
        elif opt in ("-o", "--offset"):
            baseOffset = int(arg, 0)
        elif opt in '-u':
            userApp = False

    if inputFile == '':
        print(helpMessage)
        sys.exit(2)
    else:
        if binaryFile == '':
            if '.' not in inputFile:
                binaryFile = ("%s.bco" % inputFile)
            else:
                binaryFile = ("%s.bco" % inputFile.partition('.')[0])

    try:
        ifile = open(inputFile)
        bfile = open(binaryFile, "wb")

    except:
        print("Issue opening input and output files")
        sys.exit(2)

    print("input and output opened, about to parse assembly.")
    parsed_asm = parseAsm(ifile, userApp)

    print("assembly parsed, now turning into bytecode.")

    compileAsm(parsed_asm, bfile, userApp, baseOffset)
    print("Parser finished, closing up.")

    ifile.close()
    bfile.flush()
    bfile.close()


def parseAsm(asmFile, userApp):

    parsed = programBase(userApp)

    # Preprocess the lines in the assembly file to clean things up.
    for line in asmFile:

        if line[0] == '#':
            # Comment line, go to next loop
            continue

        if '#' in line:
            # Comment exists within the line
            # Grab the portion before the comment
            line = line.partition('#')[0]

        line = line.strip('\n\r')

        if len(line) == 0:
            continue

        parsed.processLine(line)

    return parsed



def compileAsm(parsed, binFile, userApp, baseOffset):

    for func = parsed.functionList
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