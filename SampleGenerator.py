from random import randint

def FillOutput(temp, temp_range):
    output = "T"+str(temp).replace("-","m")
    for t in temp_range:
        if t!=temp:
            output+='&!'+"T"+str(t).replace("-","m")
    return output


def SampleGenerate(n,l):
    f = open("examples/WeatherForcast/sample.txt","w")
    for i in range(0,n):
        T0 = randint(1,2)
        T1 = min(max(T0+randint(-1,1),-2),2)
        temp = FillOutput(T0,range(-2,3))+"."+FillOutput(T1,range(-2,3))
        for j in range(0,l-2):
            delta = randint(0,23)
            if T1<T0:
                T0 = T1
                if delta<18:
                    T1 = max(T1-1,-2)
                elif 21<=delta<=23:
                    T1 = min(T1+1,2)
            elif T1==T0:
                T0 = T1
                if delta<8:
                    T1 = max(T1-1,-2)
                elif delta>=16:
                    T1 = min(T1+1,2)
            else:
                if delta<18:
                    T1 = min(T1+1,2)
                elif 21<=delta<=23:
                    T1 = max(T1-1,-2)
            temp+="."+FillOutput(T1,range(-2,3))
        f.write(temp+"\n")
    f.close()

if __name__ == "__main__":
    SampleGenerate(8,20)
    

