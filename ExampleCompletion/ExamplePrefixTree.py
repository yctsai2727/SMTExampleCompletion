class PFTnode(object):
    
    def __init__(self, token):
        super(PFTnode,self).__init__()
        self.id = None
        self.token = token
        self.child = []
        self.count = 0
        self.action = None

    def hasChildByID(self,c_id:int):
        if len(self.child)==0:
            return False
        for c in self.child:
            if c.id == c_id:
                return True
        return False

    def hasChildByToken(self,c_token:str):
        if len(self.child)==0:
            return False
        for c in self.child:
            if c.token == c_token:
                return True
        return False
    
    def getChild(self,token):
        if len(self.child)==0:
            return None
        for c in self.child:
            if c.token == token:
                return c
        return None

    def addWord(self,word):
        self.count+=1
        if len(word)>0:
            c = self.getChild(word[0])
            if c==None:
                c=PFTnode(word[0])
                self.child.append(c)
            c.addWord(word[1:])

class PFT(object):
    def __init__(self, samples):
        super(PFT,self).__init__()
        self.root = PFTnode(None)
        for sample in samples:
            token = sample.replace("\n","").split('.')
            self.root.addWord(token)
        self.lookup:dict[int,PFTnode] = {}
        self.NodeCount = 0
        queue = [self.root]                
        while len(queue)>0:
            node = queue.pop(0)
            self.lookup[self.NodeCount] = node
            node.id = self.NodeCount
            self.NodeCount+=1
            queue.extend(node.child)
    def __synth(self, node):
        if len(node.child)==0:
            return [node.token+"."+node.action]
        sub_words = []
        for c in node.child:
            sub_words.extend(self.__synth(c))
        if node.token == None:
            return sub_words
        new_words = []
        for word in sub_words:
            new_words.append(node.token+"."+node.action + "." + word)
        return new_words
    def synth(self):
        return self.__synth(self.root)
    
            