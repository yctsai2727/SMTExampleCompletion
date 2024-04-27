
    

class PFTnode(object):
    
    def __init__(self, token):
        super(PFTnode,self).__init__()
        self.id = None
        self.token = token
        self.child = []
        self.count = 0
    
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
            c = self.getChild(self,word[0])
            if c==None:
                c=PFTnode(word[0])
                self.child.append(c)
            c.addWord(self,word[1:])

class PFT(object):
    
    def __init__(self, samples):
        super(PFT,self).__init__()
        self.root = PFTnode(None)
        for sample in samples:
            self.root.addWord(sample)
        self.lookup:dict[int,PFTnode] = {}
        self.NodeCount = 0
        queue = [self.root]                
        while len(queue)>0:
            node = queue.pop(0)
            self.lookup[self.NodeCount] = node
            node.id = self.NodeCount
            self.NodeCount+=1
            queue.extend(node.child)
    
            