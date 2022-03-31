import sys
import getopt

from assemblercore import parseAsm, compileAsm

def main(argv):
    inputFile = ''
    binaryFile = ''
    ifile = None
    bfile = None
    osRoot = True
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
            baseOffset = int(arg, 16)
        elif opt in '-u':
            osRoot = False

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
    parsed_asm = parseAsm(ifile, osRoot)

    print("assembly parsed, now turning into bytecode.")

    compileAsm(parsed_asm, bfile, osRoot, baseOffset)
    print("Parser finished, closing up.")

    ifile.close()
    bfile.flush()
    bfile.close()


if __name__ == "__main__":
    main(sys.argv[1:])