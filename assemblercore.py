import struct


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
    variableDict = dict()
    instructionList = list()
    functionName = ""
    bytecodeList = None
    globalReference = None
    SINGLE_INPUT_INSTRUCTION = ("SET", "INC", "UINC", "SINC", "DEC", "UDEC", "SDEK" ) # TODO: Fill out full single input list
    DUAL_INPUT_INSTRUCTION = ("ADD", "UADD", "SADD", "SUB", "USUB", "SSUB")    # TODO: Fill out full dual input list
    REGISTER_LIST = ("GP1", "GP2", "GP3", "GP4", "GP5", "GP6", "GP7", "GP8")   # TODO: Fill out full register list

    def __init__(self, funName, globalRef):
        self.functionAddressBase = 0x0000
        self.labelList = list()
        self.labelList.clear()
        self.variableDict = list()
        self.variableDict.clear()
        self.instructionList = list()
        self.instructionList.clear()
        self.functionName = funName
        self.bytecodeList = bytearray()
        self.globalReference = globalRef

    def addVariable(self, name, value):
        varIndex = -1
        # Add a variable to the list, if variable already exists then return -1
        if self.getVariableIndex(name) == -1:
            varIndex = len(self.variableDict) + 1
            self.variableDict[varIndex] = (name, value)
        return varIndex

    def getVariableIndex(self, name):
        retVal = -1
        for var in self.variableDict:
            if var[1] == name:
                retVal = var[0]
        return retVal

    def addInstruction(self, instruction):

        ins = instruction.upper().split(':')
        insLen = 0

        if ins[0] in self.SINGLE_INPUT_INSTRUCTION:
            # analyze for 1 input
            if ins[1][0:2] == "@@" and self.globalReference is not None:
                # Global variable and we aren't global
                # Set RAMAdd to literal
                insLen += 2
            elif ins[1][1] == '@':
                # Local variable
                lvIndex = self.getVariableIndex(ins[1])
                if lvIndex == 1:
                    insLen += 2
                    # inc stack
                    # copy alu out to mem address
                else:
                    insLen += 3
                    # Set GP8 to Literal (2)
                    # add gp8 to stack var
                    # copy ALUOut to RAMAdd
            elif ins[1] in self.REGISTER_LIST:
                insLen += 1

            if ins[0] == "SET":
                # Add one more for the literal value to be stored at.
                insLen += 1

        elif ins[0] in self.DUAL_INPUT_INSTRUCTION:
            # analyze for 2 input

            insvar = False
            if ins[1][0:2] == "@@" and self.globalReference is not None:
                # Global variable and we aren't global
                # RAM starts at 0x4000
                # set RAMAdd to literal
                insLen += 2
                insvar = True

            if ins[1][1] == "@":
                # Local variable
                lvIndex = self.getVariableIndex(ins[1])
                insvar = True
                if lvIndex == 1:
                    insLen += 2
                    # inc stack
                    # copy alu out to mem address
                else:
                    insLen += 4
                    # set gp8 to literal
                    # add gp8 to stack var
                    # copy alu out to mem address

            elif ins[1] in self.REGISTER_LIST:
                # Register
                insLen += 1

            if ins[2][0:2] == "@@" and self.globalReference is not None:

                # Global variable and we aren't global
                if insvar:
                    # Just to add fun, we already have a variable so one of the two
                    # will need to be moved to a General Purpose Register.
                    # I don't care in this stage so just add space for it.
                    # Set RAMAdd to Literal
                    # Copy from RAMData to GP8
                    insLen += 3
                else:
                    # set RAMAdd to literal
                    insLen += 2
            if ins[2][1] == "@":
                # Local variable
                lvIndex = self.getVariableIndex(ins[1])
                insvar = True
                if lvIndex == 1:
                    insLen += 2
                    # inc stack
                    # copy alu out to mem address
                    if insvar:
                        # Copy RAMData to GP8
                        insLen += 1
                else:
                    insLen += 3
                    # set gp8 to literal
                    # add gp8 to stack var
                    # copy alu out to mem address
                    if insvar:
                        # Copy RAMData to GP8
                        insLen += 1
            elif ins[2] in self.REGISTER_LIST:
                # Register
                insLen += 1

        self.instructionList.append((instruction, insLen))
        return insLen

    def addLabel(self, name):
        # Add the label name with the instruction index

        self.labelList.append((name, len(self.instructionList) - 1))


def parseAsm(asmFile, osRoot):

    parsed = programBase(osRoot)

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


def compileAsm(parsed, binFile, osRoot, baseOffset):

    functionList = parsed.functionList

    globalFunction = functionList[0]

    processVariables(globalFunction.VariableList, osRoot)

    for func in parsed.functionList:
        for instr in func.instructionList:
            parsed_com = instr.upper().split(':')

            comm = parsed_com[0]
            if   comm == "COPY":
                data = 0x0000 | parse_loc_a(parsed_com[1]) | parse_loc_b(parsed_com[2])
            elif comm == "SET0":
                data = 0x0800 | parse_loc_b(parsed_com[1])
            elif comm == "SET1":
                data = 0x1000 | parse_loc_b(parsed_com[1])
            elif comm == "SETN":
                data = 0x1800 | parse_loc_b(parsed_com[1])
            elif comm == "UINC" or comm == "INC":
                data = 0x2000 | parse_loc_a(parsed_com[1])
            elif comm == "SINC":
                data = 0x2800 | parse_loc_a(parsed_com[1])
            elif comm == "UDEC" or comm == "DEC":
                data = 0x3000 | parse_loc_a(parsed_com[1])
            elif comm == "SDEC":
                data = 0x3800 | parse_loc_a(parsed_com[1])
            elif comm == "UADD" or comm == "ADD":
                data = 0x4000 | parse_loc_a(parsed_com[1]) | parse_loc_b(parsed_com[2])
            elif comm == "SADD":
                data = 0x4800 | parse_loc_a(parsed_com[1]) | parse_loc_b(parsed_com[2])
            elif comm == "USUB" or comm == "SUB":
                data = 0x5000 | parse_loc_a(parsed_com[1]) | parse_loc_b(parsed_com[2])
            elif comm == "SSUB":
                data = 0x5800 | parse_loc_a(parsed_com[1]) | parse_loc_b(parsed_com[2])
            elif comm == "UMUL" or comm == "MUL":
                data = 0x6000 | parse_loc_a(parsed_com[1]) | parse_loc_b(parsed_com[2])
            elif comm == "SMUL":
                data = 0x6800 | parse_loc_a(parsed_com[1]) | parse_loc_b(parsed_com[2])
            elif comm == "UDIV" or comm == "DIV":
                data = 0x7000 | parse_loc_a(parsed_com[1]) | parse_loc_b(parsed_com[2])
            elif comm == "SDIV":
                data = 0x7800 | parse_loc_a(parsed_com[1]) | parse_loc_b(parsed_com[2])
            elif comm == "AND":
                data = 0x8000 | parse_loc_a(parsed_com[1]) | parse_loc_b(parsed_com[2])
            elif comm == "OR":
                data = 0x8800 | parse_loc_a(parsed_com[1]) | parse_loc_b(parsed_com[2])
            elif comm == "NOT":
                data = 0x9000 | parse_loc_a(parsed_com[1])
            elif comm == "NEG":
                data = 0x9800 | parse_loc_a(parsed_com[1])
            elif comm == "BSL":
                data = 0xA000 | parse_loc_a(parsed_com[1])
            elif comm == "BSR":
                data = 0xA800 | parse_loc_a(parsed_com[1])
            elif comm == "SET":
                data = 0xB000 | parse_loc_b(parsed_com[1])
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


def processVariables(variableDict):

    # COPY STACKREG MEMADD

    for k in variableDict:
        # SET MEMDATA v[1] (value)
        # v = ( name, value)
        v = variableDict[k]

        # INC MEMADD
        # COPY MEMALU MEMADD

        pass



def parse_loc_a(location):

    rval = 0x0000

    if location == "RJP":
        pass
    elif location == "RJO":
        rval = 0x0010
    elif location == "RMA":
        rval = 0x0020
    elif location == "RMD":
        rval = 0x0030
    elif location == "GP1":
        rval = 0x0040
    elif location == "GP2":
        rval = 0x0050
    elif location == "GP3":
        rval = 0x0060
    elif location == "GP4":
        rval = 0x0070
    elif location == "GP5":
        rval = 0x0080
    elif location == "GP6":
        rval = 0x0090
    elif location == "GP7":
        rval = 0x00A0
    elif location == "GP8":
        rval = 0x00B0
    elif location == "RPC":
        rval = 0x00C0
    elif location == "STK":
        rval = 0x00D0
    elif location == "ALU":
        rval = 0x00E0
    elif location == "RFL":
        rval = 0x00F0

    return rval

def parse_loc_b(location):

    rval = 0x0000

    if location == "RJP":
        pass
    elif location == "RJO":
        rval = 0x0001
    elif location == "RMA":
        rval = 0x0002
    elif location == "RMD":
        rval = 0x0003
    elif location == "GP1":
        rval = 0x0004
    elif location == "GP2":
        rval = 0x0005
    elif location == "GP3":
        rval = 0x0006
    elif location == "GP4":
        rval = 0x0007
    elif location == "GP5":
        rval = 0x0008
    elif location == "GP6":
        rval = 0x0009
    elif location == "GP7":
        rval = 0x000A
    elif location == "GP8":
        rval = 0x000B
    return rval