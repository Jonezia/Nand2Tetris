# Usage: pass a directory, will parse all the .jack files in the directory into .xml files

import re
import sys
import glob

class Reader:
    def __init__(self, file):
        self.inLineCount = 0
        locator = max(file.rfind("/"),file.rfind("\\"))
        self.filename = file[locator+1:file.rfind(".")]
        self.file_in = open(file,"r")
        # Set up tokens file
        self.tokens_out = open(directory + "/_" + self.filename + "T.xml","w")
        self.tokens_out.write("")
        # Open file again, this time appending lines
        self.tokens_out = open(directory + "/_" + self.filename + "T.xml","a")
        # Set up XML output file
        self.file_out = open(directory + "/_" + self.filename + ".xml","w")
        self.file_out.write("")
        # Open file again, this time appending lines
        self.file_out = open(directory + "/_" + self.filename + ".xml","a")
        self.tokenizer = Tokenizer(self.tokens_out)
        self.parser = Parser(self.file_out)

    def run(self):
        line = self.file_in.readline()
        if not line:
            print(self.filename + " is empty")
        else:
            self.inLineCount += 1
            self.nextLine()

    def nextLine(self):
        line = self.file_in.readline()
        if not line:
            self.endOfFile()
        else:
            self.inLineCount += 1
            if not re.match(r'^\s*$', line) and line[0] != "/":
                if line.find("/") != -1:
                    line = line[:line.find("/")]
                line = line.strip()
                self.inLineCount += 1
                self.tokenizer.tokenize(line)
            self.nextLine()

    def endOfFile(self):
        self.file_in.close()
        self.tokens_out.write("</tokens>")
        self.tokens_out.close()
        self.parser.parse(self.tokenizer.tokens)


class Tokenizer:
    # Breaks each line into tokens
    def __init__(self,tokens_out):
        self.tokens = []
        self.tokens_out = tokens_out
        self.tokens_out.write("<tokens>")

    def tokenize(self,line):
        string = []
        # split by whitespace and symbols
        tempTokens = re.split("([\s\[\{\}\(\)\[\]\.\*\+\|\-,;/&<>=~])",line)
        tempTokens = [token for token in tempTokens if not token.strip() == ""]
        self.tokens += tempTokens
        for token in tempTokens:
            # If we are processing a string
            if len(string) > 0:
                # \\\\\" = \\"
                if token.endswith("\\\\\""):
                    string.append(token[:-3])
                    outString = " ".join(string)
                    self.add_token("stringConstant",outString)
                    string = []
                else:
                    string.append(token)
            else:
                if token.startswith("\\\\\""):
                    # If token is a complete string
                    if token.endswith("\\\\\""):
                        self.add_token("stringConstant",token[4:-3])
                    else:
                        string.append(token[4:])
                        continue
                elif token in ["class","constructor","function","method","field",
                "static","var","int","char","boolean","void","true","false",
                "null","this","let","do","if","else","while","return"]:
                    self.add_token("keyword",token)
                elif token in ["{","}","(",")","[","]",".",",",";","+","-","*",
                "/","&","|","<",">","=","~"]:
                    self.add_token("symbol",token)
                elif token.isdigit():
                    self.add_token("integerConstant",token)
                else:
                    self.add_token("identifier",token)

    def add_token(self,tokenType,tokenName):
        self.tokens_out.write(f"\t<{tokenType}>{tokenName}</{tokenType}>\n")

class Parser:
    # Parses tokens into xml tree
    def __init__(self,file_out):
        self.file_out = file_out

    def parse(self,tokens):
        pass

# Main
directory = sys.argv[1]
if directory[-1] == "/":
    directory = directory[:-1]
files = [f for f in glob.glob(directory + "/*.jack")]
if len(files) is 0:
    print("No .jack files found in this directory")
else:
    for file in files:
        jackAnalyser = Reader(file)
        jackAnalyser.run()
        print(jackAnalyser.filename + " successful, " + str(jackAnalyser.inLineCount) +
        " lines in, " + str(len(jackAnalyser.tokenizer.tokens)) + " tokens generated")
