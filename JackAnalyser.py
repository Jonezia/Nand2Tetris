# Usage: pass a directory, will parse all the .jack files in the directory into .xml files

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
        self.parser.parse()


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
        self.currentTokenType = None
        self.currentTokenName = None
        self.tokens = tokens
        self.get_next_token()

    def get_next_token(self):
        self.currentTokenType, self.currentTokenName = self.tokens[pointer]
        pointer += 1
        return self.currentTokenType,self.currentTokenName

    def parse(self):
        if self.currentTokenType == "keyword":
            if self.currentTokenName == "class":
                self.parseClass()
            elif self.currentTokenName in ["static","field"]:
                self.parseClassVarDec()
            elif self.currentTokenName in ["constructor","function","method","void"]:
                self.parseSubRoutineDec()
            elif self.currentTokenName == "var":
                self.parseVarDec()
        else:
            self.error_message("expected keyword")

    def lookfor(mode,name,type,errMessage = False):
        if mode == "name":
            if self.currentTokenName == name:
                self.add_token(self.currentTokenType,name)
        elif mode == "type":
            if self.currentTokenType == type:
                self.add_token(type,self.currentTokenName)
        if errMessage:
            self.error_message(errMessage)

    def parseMultiple(self,function):
        if function():
            self.parseMultiple(function)

    def parseClass(self):
        # 'class' className '{' classVarDec* subroutineDec* '}'
        if self.currentTokenName == "class":
            self.file_out.write("<class>\n")
            self.add_token("keyword","class")
            self.get_next_token()
            # className: identifer
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            else:
                self.error_message("expected className identifier in class declaration")
            self.get_next_token()
            # '{' classVarDec* subroutineDec* '}'
            if self.currentTokenName == "{":
                self.add_token("symbol","{")
            else:
                self.error_message("expected { in class declaration")
            self.get_next_token()
            self.parseMultiple(self.parseClassVarDec)
            self.parseMultiple(self.parseSubroutineDec)
            if self.currentTokenName == "}":
                self.add_token("symbol","}")
            else:
                self.error_message("expected } in class declaration")
            self.file_out.write("</class>\n")
            self.get_next_token()
            return True
        else:
            return False

    def parseClassVarDec(self):
        # ('static' | 'field') type varName (',' varName)* ';'
        if self.currentTokenName in ["static","field"]:
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
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            else:
                self.error_message("Expected variable name identifier in class \
                variable declaration")
            self.get_next_token()
            # (',' varName)* ';'
            while self.currentTokenName == ",":
                self.add_token("symbol",",")
                self.get_next_token()
                if self.currentTokenType == "identifier":
                    self.add_token("identifier",self.currentTokenName)
                else:
                    self.error_message("Expected variable name identifier after \
                    comma in class variable declaration")
                self.get_next_token()
            if self.currentTokenName == ";":
                self.add_token("symbol",";")
            else:
                self.error_message("Expected ; after class variable declaration")
            self.file_out.write("</classVarDec>\n")
            self.get_next_token()
            return True
        else:
            return False

    def parseSubroutineDec(self):
        # ('constructor' | 'function' | 'method') ('void' | type) subroutineName
        # '(' parameterList ')' subroutineBody
        if self.currentTokenName in ["constructor","function","method"]:
            self.file_out.write("<subroutineDec>\n")
            self.add_token("keyword",self.currentTokenName)
            self.get_next_token()
            # ('void' | type)
            # type: 'int' | 'char' | 'boolean' | className className: identifier
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            elif self.currentTokenName in ["int","char","boolean","void"]:
                self.add_token("keyword",self.currentTokenName)
            else:
                self.error_message("Expected type or void in subroutine declaration")
            self.get_next_token()
            # subroutineName: identifier
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            else:
                self.error_message("expected subroutine name identifier in \
                subroutine declaration")
            self.get_next_token()
            # '(' parameterList ')'
            if self.currentTokenName == "(":
                self.add_token("symbol","(")
            else:
                self.error_message("expected ( in subroutine declaration")
            self.get_next_token()
            self.parseParameterList()
            if self.currentTokenName == ")":
                self.add_token("symbol",")")
            else:
                self.error_message("expected ) in subroutine declaration")
            self.get_next_token()
            # subroutineBody: '{' varDec* statements '}'
            if self.currentTokenName == "{":
                self.add_token("symbol","{")
            else:
                self.error_message("expected { in subroutine declaration")
            self.get_next_token()
            self.parseMultiple(self.parseVarDec)
            self.parseStatements()
            self.get_next_token()
            if self.currentTokenName == "}":
                self.add_token("symbol","}")
            else:
                self.error_message("expected } in subroutine declaration")
            self.file_out.write("</subroutineDec>\n")
            self.get_next_token()
            return True
        else:
            return False

    def parseParameterList(self):
        # ((type varName)(',' type varName)*)?
        self.file_out.write("<parameterList>\n")
        if self.currentTokenType == "identifier" or self.currentTokenName
        in ["int","char","boolean"]:
            # (type varName) varName: identifier
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            elif self.currentTokenName in ["int","char","boolean"]:
                self.add_token("keyword",self.currentTokenName)
            self.get_next_token()
            if self.currentTokenType == "identifier":
                self.add_token("identifer",self.currentTokenName)
            else:
                self.error_message("expected varName identifier in parameter list")
            self.get_next_token()
            # (',' type varName)* varName: identifier
            while self.currentTokenName == ",":
                self.add_token("symbol",",")
                self.get_next_token()
                if self.currentTokenType == "identifier":
                    self.add_token("identifier",self.currentTokenName)
                elif self.currentTokenName in ["int","char","boolean"]:
                    self.add_token("keyword",self.currentTokenName)
                else:
                    self.error_message("expected type after comma in parameter list")
                self.get_next_token()
                if self.currentTokenType == "identifier":
                    self.add_token("identifier",self.currentTokenName)
                else:
                    self.error_message("expected varName identifier after comma \
                    in parameter list")
                self.get_next_token()
        self.file_out.write("</parameterList>\n")

    def parseVarDec(self):
        # 'var' type varName (',' varName)* ';'
        if self.currentTokenName == "var":
            self.file_out.write("<varDec>\n")
            self.add_token("keyword","var")
            self.get_next_token()
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            elif self.currentTokenName in ["int","char","boolean"]:
                self.add_token("keyword",self.currentTokenName)
            else:
                self.error_message("expected type in variable declaration")
            self.get_next_token()
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            else:
                self.error_message("expected varName identifer in variable declaration")
            self.get_next_token()
            while self.currentTokenName == ",":
                self.add_token("symbol",",")
                self.get_next_token()
                if self.currentTokenType == "identifier":
                    self.add_token("identifier",self.currentTokenName)
                else:
                    self.error_message("expected varName identifier after comma \
                    in variable declaration")
                self.get_next_token()
            if self.currentTokenName == ";":
                self.add_token("symbol",";")
            else:
                self.error_message("expected semicolon after variable declaration")
            self.file_out.write("</varDec>\n")
            self.get_next_token()
            return True
        else:
            return False

    def parseStatements(self):
        # statement*
        # statement: letStatement | if statement | whileStatement | doStatement
        # returnStatement
        self.file_out.write("<statements>\n")
        if self.parseStatement():
            self.parseStatement()
        self.file_out.write("</statements>\n")

    def parseStatement(self):
        # helper function for parseStatements
        if parseLetStatement():
            return True
        elif parseIfStatement():
            return True
        elif parseWhileStatement():
            return True
        elif parseDoStatement():
            return True
        elif parseReturnStatement():
            return True
        else:
            return False

    def parseLetStatement(self):
        # 'let' varName ('[' expression ']')? '=' expression ';'
        if self.currentTokenName == "let":
            self.file_out.write("<letStatement>\n")
            self.add_token("keyword","let")
            self.get_next_token()
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            else:
                self.error_message("expected varName identifier after let")
            self.get_next_token()
            if self.currentTokenName == "[":
                self.add_token("symbol","[")
                self.get_next_token()
                self.parseExpression()
                if self.currentTokenName == "]":
                    self.add_token("symbol","]")
                else:
                    self.error_message("expected ] after [ in let statement")
                self.get_next_token()
            if self.currentTokenName == "=":
                self.add_token("symbol","=")
            else:
                self.error_message("expected = in let statement")
            self.get_next_token()
            self.parseExpression()
            if self.currentTokenName == ";":
                self.add_token("symbol",";")
            else:
                self.error_message("expected ; after let statement")
            self.file_out.write("</letStatement>\n")
            self.get_next_token()
            return True
        else:
            return False

    def parseIfStatement(self):
        # 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        if self.currentTokenName == "if":
            self.file_out.write("<ifStatement>\n")
            self.add_token("keyword","if")
            self.get_next_token()
            if self.currentTokenName == "(":
                self.add_token("symbol","(")
            else:
                self.error_message("expected ( in if statement")
            self.get_next_token()
            self.parseExpression()
            if self.currentTokenName == ")":
                self.add_token("symbol",")")
            else:
                self.error_message("expected ) in if statement")
            self.get_next_token()
            if self.currentTokenName == "{":
                self.add_token("symbol","{")
            else:
                self.error_message("expected { in if statement")
            self.parseStatements()
            if self.currentTokenName == "{":
                self.add_token("symbol","}")
            else:
                self.error_message("expected } in if statement")
            self.get_next_token()
            if self.currentTokenName == "else":
                self.add_token("keyword","else")
                self.get_next_token()
                if self.currentTokenName == "{":
                    self.add_token("symbol","{")
                else:
                    self.error_message("expected { after else in if statement")
                self.get_next_token()
                self.parseStatements()
                if self.currentTokenName == "}":
                    self.add_token("symbol","}")
                else:
                    self.error_message("expected } after else in if statement")
                self.get_next_token()
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
            if self.currentTokenName == "(":
                self.add_token("symbol","(")
            else:
                self.error_message("expected ( in while statement")
            self.get_next_token()
            self.parseExpression()
            if self.currentTokenName == ")":
                self.add_token("symbol",")")
            else:
                self.error_message("expected ) in while statement")
            self.get_next_token()
            self.file_out.write("</whileStatement>\n")
            self.get_next_token()
            return True
        else:
            return False

    def parseDoStatement(self):
        # 'do' subroutineCall ';'
        # subroutineCall: subroutineName '(' expressionList ')' | (className |
        # varName) '.' subroutineName '(' expressionList ')'
        # subroutineName, varName, className: identifier
        if self.currentTokenName == "do":
            self.file_out.write("<doStatement>\n")
            self.file_out.write("</doStatement>\n")
            self.get_next_token()
            return True
        else:
            return False

    def parseReturnStatement(self):
        # 'return' expression? ';'
        if self.currentTokenName == "return":
            self.file_out.write("<returnStatement>\n")
            self.file_out.write("</returnStatement>\n")
            self.get_next_token()
            return True
        else:
            return False

    def parseExpression(self):
        # term (op term)*
        # op: '+', '-', '*', '/', '&', '|', '<', '>', '='
        self.file_out.write("<expression>\n")
        self.file_out.write("</expression>\n")

    def parseTerm(self):
        # integerConstant | stringConstant | keywordConstant | varName |
        # varName '[' expression ']' | subroutineCall | '(' expression ')' |
        # unaryOp term
        # keywordConstant: 'true' | 'false' | 'null' | 'this'
        # unaryOp: '-', '~'
        self.file_out.write("<term>\n")
        self.file_out.write("</term>\n")

    def parseExpressionList(self):
        # (expression (',' expression)*)?
        self.file_out.write("<expressionList>\n")
        self.file_out.write("</expressionList>\n")

    def error_message(self,message):
        print("expected " + message + " token " + self.pointer)

    def add_token(self,tokenType,tokenName):
        self.file_out.write(f"<{tokenType}>{tokenName}</{tokenType}>\n")

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
