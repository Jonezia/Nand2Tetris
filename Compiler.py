# Usage: pass a directory, will parse all the .jack files in the directory into vm code (.vml files)

import re
import sys
import glob

class Reader:
    def __init__(self, file):
        self.inLineCount = 0
        self.blockComment = False
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

    def run(self):
        line = self.file_in.readline()
        if not line:
            self.endOfFile()
        else:
            line = line.strip()
            if not line == "" and not line.startswith("//"):
                if self.blockComment == False:
                    if line.startswith("/*"):
                        self.blockComment = True
                    else:
                        if line.find("//") != -1:
                            line = line[:line.find("//")]
                        self.inLineCount += 1
                        self.tokenizer.tokenize(line)
                if line.endswith("*/"):
                    self.blockComment = False
            self.run()

    def endOfFile(self):
        self.file_in.close()
        self.tokens_out.write("</tokens>")
        self.tokens_out.close()
        self.parser = Parser(self.file_out,self.tokenizer.tokens)
        self.parser.parseClass()


class Tokenizer:
    # Breaks each line into tokens
    def __init__(self,tokens_out):
        self.num_tokens = 0
        self.tokens = []
        self.tokens_out = tokens_out
        self.tokens_out.write("<tokens>\n")

    def tokenize(self,line):
        string = []
        # split by whitespace and symbols
        tempTokens = re.split("([\s\[\{\}\(\)\[\]\.\*\+\|\-,;/&<>=~])",line)
        tempTokens = [token for token in tempTokens if not token.strip() == ""]
        for token in tempTokens:
            # If we are processing a string
            if len(string) > 0:
                if token.endswith("\""):
                    string.append(token[:-1])
                    outString = " ".join(string)
                    self.add_token("stringConstant",outString)
                    string = []
                else:
                    string.append(token)
            else:
                if token.startswith("\""):
                    # If token is a complete string
                    if token.endswith("\""):
                        self.add_token("stringConstant",token[1:-1])
                    else:
                        string.append(token[1:])
                        continue
                elif token in ["class","constructor","function","method","field",
                "static","var","int","char","boolean","void","true","false",
                "null","this","let","do","if","else","while","return"]:
                    self.add_token("keyword",token)
                elif token in ["{","}","(",")","[","]",".",",",";","+","-","*",
                "/","&","|","<",">","=","~"]:
                    if token == "&":
                        self.add_token("symbol","&amp;")
                    elif token == "<":
                        self.add_token("symbol","&lt;")
                    elif token == ">":
                        self.add_token("symbol","&gt;")
                    else:
                        self.add_token("symbol",token)
                elif token.isdigit():
                    self.add_token("integerConstant",token)
                else:
                    self.add_token("identifier",token)

    def add_token(self,tokenType,tokenName):
        self.num_tokens += 1
        self.tokens_out.write(f"<{tokenType}>{tokenName}</{tokenType}>\n")
        self.tokens.append([tokenType,tokenName])

class Parser:
    # Parses tokens into xml tree
    def __init__(self,file_out,tokens):
        self.file_out = file_out
        self.pointer = 0
        self.symbolTable = SymbolTable()
        self.currentTokenType = None
        self.currentTokenName = None
        self.tokens = tokens
        self.get_next_token()

    def get_next_token(self):
        if self.pointer != len(self.tokens) - 1:
            self.currentTokenType, self.currentTokenName = self.tokens[self.pointer]
            self.pointer += 1
            return self.currentTokenType,self.currentTokenName

    def lookfor(self,mode,name,type,errMessage):
        if mode == "name":
            if self.currentTokenName == name:
                self.add_token(self.currentTokenType,name)
            else:
                if errMessage:
                    self.error_message(errMessage)
        elif mode == "type":
            if self.currentTokenType == type:
                self.add_token(type,self.currentTokenName)
            else:
                if errMessage:
                    self.error_message(errMessage)
        self.get_next_token()

    def parseClass(self):
        # 'class' className '{' classVarDec* subroutineDec* '}'
        if self.currentTokenName == "class":
            self.file_out.write("<class>\n")
            self.add_token("keyword","class")
            self.get_next_token()
            self.lookfor("type",None,"identifier","className identifier in " +
            "class declaration")
            self.lookfor("name","{",None,"{ in class declaration")
            while True:
                if not self.parseClassVarDec():
                    break
            while True:
                if not self.parseSubroutineDec():
                    break
            self.lookfor("name","}",None,"} in class declaration")
            self.file_out.write("</class>\n")
            self.get_next_token()
            return True
        else:
            return False

    def parseClassVarDec(self):
        # ('static' | 'field') type varName (',' varName)* ';'
        if self.currentTokenName in ["static","field"]:
            category = self.currentTokenName
            self.file_out.write("<classVarDec>\n")
            self.add_token("keyword",self.currentTokenName)
            self.get_next_token()
            # type: 'int' | 'char' | 'boolean' | className
            # className: identifier
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            elif self.currentTokenName in ["int","char","boolean"]:
                self.add_token("keyword",self.currentTokenName)
            else:
                self.error_message("Expected type in class variable declaration")
            self.get_next_token()
            # varName: identifier
            self.lookfor("type",None,"identifier","variable name identifier " +
            "in class variable declaration")
            # (',' varName)* ';'
            while self.currentTokenName == ",":
                self.add_token("symbol",",")
                self.get_next_token()
                self.lookfor("type",None,"identifier","variable name " +
                "identifier after comma in class variable declaration")
            self.lookfor("name",";",None,"; after class variable declaration")
            self.file_out.write("</classVarDec>\n")
            return True
        else:
            return False

    def lookfortype(self,void,errMessage):
        # helper function to parse (type)
        if void:
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            elif self.currentTokenName in ["int","char","boolean","void"]:
                self.add_token("keyword",self.currentTokenName)
            else:
                self.error_message("Expected type or void " + errMessage)
        else:
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            elif self.currentTokenName in ["int","char","boolean"]:
                self.add_token("keyword",self.currentTokenName)
            else:
                self.error_message("Expected type " + errMessage)
        self.get_next_token()

    def parseSubroutineDec(self):
        # ('constructor' | 'function' | 'method') ('void' | type) subroutineName
        # '(' parameterList ')' subroutineBody
        if self.currentTokenName in ["constructor","function","method"]:
            self.file_out.write("<subroutineDec>\n")
            self.add_token("keyword",self.currentTokenName)
            self.get_next_token()
            # ('void' | type)
            # type: 'int' | 'char' | 'boolean' | className className: identifier
            self.lookfortype(True,"in subroutine declaration")
            # subroutineName: identifier
            self.lookfor("type",None,"identifier","subroutine name " +
            "identifier in subroutine declaration")
            # '(' parameterList ')'
            self.lookfor("name","(",None,"( in subroutine declaration")
            self.parseParameterList()
            self.lookfor("name",")",None,") in subroutine declaration")
            # subroutineBody: '{' varDec* statements '}'
            self.file_out.write("<subroutineBody>\n")
            self.lookfor("name","{",None,"{ in subroutine declaration")
            while True:
                if not self.parseVarDec():
                    break
            self.parseStatements()
            self.lookfor("name","}",None,"} in subroutine declaration")
            self.file_out.write("</subroutineBody>\n")
            self.file_out.write("</subroutineDec>\n")
            return True
        else:
            return False

    def parseParameterList(self):
        # ((type varName)(',' type varName)*)?
        self.file_out.write("<parameterList>\n")
        if self.currentTokenType == "identifier" or self.currentTokenName \
        in ["int","char","boolean"]:
            # (type varName) varName: identifier
            self.lookfortype(False,"in parameter list")
            self.lookfor("type",None,"identifier","varName identifier in parameter list")
            # (',' type varName)* varName: identifier
            while self.currentTokenName == ",":
                self.add_token("symbol",",")
                self.get_next_token()
                self.lookfortype(False,"in parameter list after ,")
                self.lookfor("type",None,"identifier","varName identifier " +
                "after comma in parameter list")
        self.file_out.write("</parameterList>\n")

    def parseVarDec(self):
        # 'var' type varName (',' varName)* ';'
        if self.currentTokenName == "var":
            self.file_out.write("<varDec>\n")
            self.add_token("keyword","var")
            self.get_next_token()
            self.lookfortype(False,"in variable declaration")
            self.lookfor("type",None,"identifier","varName identifer in " +
            "variable declaration")
            while self.currentTokenName == ",":
                self.add_token("symbol",",")
                self.get_next_token()
                self.lookfor("type",None,"identifier","varName identifier " +
                "after comma in variable declaration")
            self.lookfor("name",";",None,"semicolon after variable declaration")
            self.file_out.write("</varDec>\n")
            return True
        else:
            return False

    def parseStatements(self):
        # statement*
        # statement: letStatement | if statement | whileStatement | doStatement
        # returnStatement
        self.file_out.write("<statements>\n")
        while True:
            if not self.parseStatement():
                break
        self.file_out.write("</statements>\n")

    def parseStatement(self):
        # helper function for parseStatements
        if self.parseLetStatement():
            return True
        elif self.parseIfStatement():
            return True
        elif self.parseWhileStatement():
            return True
        elif self.parseDoStatement():
            return True
        elif self.parseReturnStatement():
            return True
        else:
            return False

    def parseLetStatement(self):
        # 'let' varName ('[' expression ']')? '=' expression ';'
        if self.currentTokenName == "let":
            self.file_out.write("<letStatement>\n")
            self.add_token("keyword","let")
            self.get_next_token()
            self.lookfor("type",None,"identifier","varName identifier after let")
            if self.currentTokenName == "[":
                self.add_token("symbol","[")
                self.get_next_token()
                self.parseExpression()
                self.lookfor("name","]",None,"] after [ in let statement]")
            self.lookfor("name","=",None,"= in let statement")
            self.parseExpression()
            self.lookfor("name",";",None,"; after let statement")
            self.file_out.write("</letStatement>\n")
            return True
        else:
            return False

    def parseIfStatement(self):
        # 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        if self.currentTokenName == "if":
            self.file_out.write("<ifStatement>\n")
            self.add_token("keyword","if")
            self.get_next_token()
            self.lookfor("name","(",None,"( in if statement)")
            self.parseExpression()
            self.lookfor("name",")",None,") in if statement")
            self.lookfor("name","{",None,"{ in if statement")
            self.parseStatements()
            self.lookfor("name","}",None,"} in if statement")
            if self.currentTokenName == "else":
                self.add_token("keyword","else")
                self.get_next_token()
                self.lookfor("name","{",None,"{ after else in if statement")
                self.parseStatements()
                self.lookfor("name","}",None,"} after else in if statement")
            self.file_out.write("</ifStatement>\n")
            return True
        else:
            return False

    def parseWhileStatement(self):
        # 'while' '(' expression ')' '{' statements '}'
        if self.currentTokenName == "while":
            self.file_out.write("<whileStatement>\n")
            self.add_token("keyword","while")
            self.get_next_token()
            self.lookfor("name","(",None,"( in while statement")
            self.parseExpression()
            self.lookfor("name",")",None,") in while statement")
            self.lookfor("name","{",None,"{ in while statement")
            self.parseStatements()
            self.lookfor("name","}",None,"} in while statement")
            self.file_out.write("</whileStatement>\n")
            return True
        else:
            return False

    def parseSubroutineCall(self,location):
        # helper function for parseDoStatement and parseTerm
        if self.currentTokenName == ".":
            self.add_token("symbol",".")
            self.get_next_token()
            self.lookfor("type",None,"identifier","subroutineName identifier " +
            "after . in do statement")
        self.lookfor("name","(",None,"( in " + location)
        self.parseExpressionList()
        self.lookfor("name",")",None,") after ( in " + location)

    def parseDoStatement(self):
        # 'do' subroutineCall ';'
        # subroutineCall: subroutineName '(' expressionList ')' | (className |
        # varName) '.' subroutineName '(' expressionList ')'
        # subroutineName, varName, className: identifier
        if self.currentTokenName == "do":
            self.file_out.write("<doStatement>\n")
            self.add_token("keyword","do")
            self.get_next_token()
            # subroutine call
            self.lookfor("type",None,"identifier","subroutineName, className " +
            "or varName identifier in do statement")
            self.parseSubroutineCall("do statement")
            self.lookfor("name",";",None,"; after do statement")
            self.file_out.write("</doStatement>\n")
            return True
        else:
            return False

    def parseReturnStatement(self):
        # 'return' expression? ';'
        if self.currentTokenName == "return":
            self.file_out.write("<returnStatement>\n")
            self.add_token("keyword","return")
            self.get_next_token()
            if self.currentTokenType in ["integerConstant","stringConstant", \
            "identifier"] or self.currentTokenName in ["true","false","null", \
            "this","(","-","~"]:
                self.parseExpression()
            self.lookfor("name",";",None,"; after return statement")
            self.file_out.write("</returnStatement>\n")
            return True
        else:
            return False

    def parseExpression(self):
        # term (op term)*
        # op: '+', '-', '*', '/', '&', '|', '<', '>', '='
        self.file_out.write("<expression>\n")
        if self.parseTerm():
            while self.currentTokenName in ["+","-","*","/","&amp;","|","&lt;","&gt;","="]:
                self.add_token("symbol",self.currentTokenName)
                self.get_next_token()
                self.parseTerm()
            self.file_out.write("</expression>\n")
            return True
        else:
            self.file_out.write("</expression>\n")
            return False

    def parseTerm(self):
        # integerConstant | stringConstant | keywordConstant | varName |
        # varName '[' expression ']' | subroutineCall | '(' expression ')' |
        # unaryOp term

        # keywordConstant: 'true' | 'false' | 'null' | 'this'
        # unaryOp: '-', '~'
        # subroutineCall: subroutineName '(' expressionList ')' | (className |
        # varName) '.' subroutineName '(' expressionList ')'
        self.file_out.write("<term>\n")
        if self.currentTokenType in ["integerConstant","stringConstant"]:
            self.add_token(self.currentTokenType,self.currentTokenName)
            self.get_next_token()
            self.file_out.write("</term>\n")
            return True
        elif self.currentTokenName in ["true","false","null","this"]:
            self.add_token("keyword",self.currentTokenName)
            self.get_next_token()
            self.file_out.write("</term>\n")
            return True
        elif self.currentTokenType == "identifier":
            self.add_token("identifier",self.currentTokenName)
            self.get_next_token()
            if self.currentTokenName == "[":
                self.add_token("symbol","[")
                self.get_next_token()
                self.parseExpression()
                self.lookfor("name","]",None,"] after [ in term")
            elif self.currentTokenName in ["(","."]:
                self.parseSubroutineCall("term")
            self.file_out.write("</term>\n")
            return True
        elif self.currentTokenName == "(":
            self.add_token("symbol","(")
            self.get_next_token()
            self.parseExpression()
            self.lookfor("name",")",None,"expected ) after expression in term")
            self.file_out.write("</term>\n")
            return True
        elif self.currentTokenName in ["-","~"]:
            self.add_token("symbol",self.currentTokenName)
            self.get_next_token()
            self.parseTerm()
            self.file_out.write("</term>\n")
            return True
        else:
            self.file_out.write("</term>\n")
            return False

    def parseExpressionList(self):
        # (expression (',' expression)*)?
        self.file_out.write("<expressionList>\n")
        if self.currentTokenType in ["integerConstant","stringConstant", \
        "identifier"] or self.currentTokenName in ["true","false","null", \
        "this","(","-","~"]:
            self.parseExpression()
            while self.currentTokenName == ",":
                self.add_token("symbol",",")
                self.get_next_token()
                self.parseExpression()
            self.file_out.write("</expressionList>\n")
            return True
        else:
            self.file_out.write("</expressionList>\n")
            return False

    def error_message(self,message):
        print("expected " + message + " token " + str(self.pointer))

    def add_token(self,tokenType,tokenName,classSub=None,identifier = False):
        self.file_out.write(f"<{tokenType}>{tokenName}</{tokenType}>\n")

class SymbolTable:
    def__init__(self):
        self.fieldCount = 0
        self.staticCount = 0
        self.argCount = 0
        self.varCount = 0
        self.classSymbolTable = {}
        self.subroutineSymbolTable = {}

    def startSubroutine(self):
        self.subroutineArgCount = 0
        self.subroutineVarCount = 0
        self.subroutineSymbolTable = {}

    def define(self,name,type,kind):
        if kind in ["field","static"]:
            self.classSymbolTable[name] = [type,kind,self.getCount(kind)]
        if kind in ["arg","var"]:
            self.subroutineSymbolTable[name] = [type,kind,self.getCount(kind)]
        self.getCount(kind) = self.getCount(kind) + 1

    def get(self,name):
        return self.subroutineSymbolTable[name]

    def getCount(self,kind):
        if kind == "field":
            return self.fieldCount
        elif kind == "static":
            return self.staticCount
        elif kind == "arg":
            return self.argCount
        elif kind == "var":
            return self.varCount

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
        " lines in, " + str(jackAnalyser.tokenizer.num_tokens) + " tokens generated")
