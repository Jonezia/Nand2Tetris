# Usage: enter a file location, will parse the .asm file into a .hack file,
# containing an machine code version of the assembly program
# ASSEMBLY CODE -> MACHINE CODE

import re
print("filename: ")
filename = input()
file_in = open(filename + ".asm","r")
# Overwrite file as empty if existing
file_out = open(filename + ".hack","w")
file_out.write("")
# Open file again, this time appending lines
file_out = open(filename + ".hack","a")
# Initialises first line and line number
line = file_in.readline()
lineNo = 0

variableRegister = 16

def binaryInstruction(line):
    if line[0] == "@":
        return AInstruction(line)
    else:
        return CInstruction(line)

def AInstruction(line):
    global variableRegister
    value = line[1:]
    if value.isdigit():
        Avalue = value
    elif value in symbols:
        # If it's already in symbols, it's a label
        Avalue = symbols[value]
    else:
        #If it's not in symbols, it's a new variable declaration
        Avalue = variableRegister
        symbols[value] = variableRegister
        variableRegister += 1
    # Turns A-value into 15-bit binary with padding of 0s on the left, prepends 0
    return "0" + "{:0>15b}".format(int(Avalue))

def CInstruction(line):
    # Split C instruction into dest, comp, jump
    splitEquals = line.split("=")
    if len(splitEquals) < 2:
        dest = "null"
    else:
        dest = splitEquals[0].strip()
    splitSemicolon = splitEquals[-1].split(";")
    if len(splitSemicolon) < 2:
        jump = "null"
    else:
        jump = splitSemicolon[-1].strip()
    comp = splitSemicolon[0].strip()
    jumpDictionary = {
        "null": "000",
        "JGT": "001",
        "JEQ": "010",
        "JGE": "011",
        "JLT": "100",
        "JNE": "101",
        "JLE": "110",
        "JMP": "111"
    }

    destDictionary = {
        "null": "000",
        "M": "001",
        "D": "010",
        "MD": "011",
        "A": "100",
        "AM": "101",
        "AD": "110",
        "AMD": "111"
    }
    compDictionary = {
        "0": "101010",
        "1": "111111",
        "-1": "111010",
        "D": "001100",
        "A": "110000",
        "M": "110000",
        "!D": "001101",
        "!A": "110001",
        "!M": "110001",
        "-D": "001111",
        "-A": "110011",
        "-M": "110011",
        "D+1": "011111",
        "A+1": "110111",
        "M+1": "110111",
        "D-1": "001110",
        "A-1": "110010",
        "M-1": "110010",
        "D+A": "000010",
        "D+M": "000010",
        "D-A": "010011",
        "D-M": "010011",
        "A-D": "000111",
        "M-D": "000111",
        "D&A": "000000",
        "D&M": "000000",
        "D|A": "010101",
        "D|M": "010101"
    }
    if "M" in comp:
        a = "1"
    else:
        a = "0"
    return "111" + a + compDictionary[comp] + destDictionary[dest] + jumpDictionary[jump]

symbols = {
    "R0": 0,
    "R1": 1,
    "R2": 2,
    "R3": 3,
    "R4": 4,
    "R5": 5,
    "R6": 6,
    "R7": 7,
    "R8": 8,
    "R9": 9,
    "R10": 10,
    "R11": 11,
    "R12": 12,
    "R13": 13,
    "R14": 14,
    "R15": 15,
    "SCREEN": 16384,
    "KBD": 24576,
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4
}

lines = []
# Creating lines array
while line:
    line = line.strip()
    # Checks the line isn't empty or a comment
    if not re.match(r'^\s*$', line) and line[0] != "/":
        if line.find("/") != -1:
            line = line[:line.find("/")]
        lines.append(line)
    # Goes to next line
    line = file_in.readline()

# Adding labels to symbols table
for line in lines:
    if line[0] == "(":
        #handle label
        label = line[1:-1]
        symbols[label] = lineNo
    else:
        lineNo += 1

# Get rid of labels
lines = [line for line in lines if not line[0]=="("]

for line in lines:
    line = binaryInstruction(line)
    file_out.write(line.strip() + "\n")
