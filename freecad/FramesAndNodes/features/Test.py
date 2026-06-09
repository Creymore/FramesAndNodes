import math
from ifcopenshell.express.bootstrap import found
import FreeCAD as App  # ty:ignore[unresolved-import]
from itertools import combinations  # CODE-AUDIT: unused import in KnotLogic.py.
from itertools import permutations
from itertools import combinations_with_replacement

# Test Data

Knot1 = [
    {
        "Direction": App.Vector(1,0,0)	, # Direction Always Points away from the Knots center
        "Offset": App.Vector(0,0,0)	,
        "Type": "x"						,
        "Rotation":0					, #Should this be just the direction of the X or Y Axis of the Body
        "Nsym":4						, # How often the cross section Matches itself along a 360 deg turn around its Geometric Center
    },
    {
        "Direction": App.Vector(0,1,0) ,
        "Offset": App.Vector(0,0,0)    ,
        "Type": "x"				        ,
        "Rotation":0			       	,
        "Nsym":4
    },
    {
        "Direction": App.Vector(0,0,1),
        "Offset": App.Vector(0,0,0)    ,
        "Type": "x"			        	,
        "Rotation":0				,
        "Nsym":4
    }
]

Knot2 = [
    {
        "Direction": App.Vector(-1,0,0)	, 
        "Offset": App.Vector(0,0,0)	,
        "Type": "x"						,
        "Rotation":0					, 
        "Nsym":4						, 
    },
    {
        "Direction": App.Vector(0,-1,0) ,
        "Offset": App.Vector(0,0,0)    ,
        "Type": "x"				        ,
        "Rotation":0			       	,
        "Nsym":4
    },
    {
        "Direction": App.Vector(0,0,-1),
        "Offset": App.Vector(0,0,0)    ,
        "Type": "x"			        	,
        "Rotation":0				,
        "Nsym":4
    }
]

Knot1S1 =[Knot1[0],Knot1[1],Knot1[2]]
Knot1S2 =[Knot1[0],Knot1[2],Knot1[1]]
Knot1S3 =[Knot1[1],Knot1[0],Knot1[2]]
Knot1S4 =[Knot1[1],Knot1[2],Knot1[0]]
Knot1S5 =[Knot1[2],Knot1[1],Knot1[0]]
Knot1S6 =[Knot1[2],Knot1[0],Knot1[1]]

from KnotLogic import FindallMatches2 as TestF  # ty:ignore[unresolved-import]
from KnotLogic import FindAxisAngle2,matrixToAxisAngle  # ty:ignore[unresolved-import]
from utils.utils import copyVec  # ty:ignore[unresolved-import]


print("Knot1S1")
TestF(Knot2,Knot1S1)
print("Knot1S2")
TestF(Knot2,Knot1S2)
print("Knot1S3")
TestF(Knot2,Knot1S3)
print("Knot1S4")
TestF(Knot2,Knot1S4)
print("Knot1S5")
VaildTransformations = TestF(Knot2,Knot1S5)
print("Knot1S6")
TestF(Knot2,Knot1S6)

def FindallMatches4(K1,K2,tol=1e-6):
    '''
    K1: Knot1 Stationary,
    K2: Knot2 gets Transformed
    description:
    Finds all the matches, where K2 gets Transformed into K1 successfully
    retrun: tuple((App.Vector,float),...)
    '''
    Results = []
    N = len(K1)
    for k in range(N):
        B1 = K1[k]["Direction"]
        for i in range(N):
            B2 = K1[i]["Direction"]
            for j in range(N):
                A1 = K2[j]["Direction"]
                for l in range(N):
                    A2 = K2[l]["Direction"]
                    # print(f"{k}{i}{j}{l}")
                    AAM = FindAxisAngle2(A1,B1,A2,B2,matrix=True)
                    if AAM is not False:
                        
                        allMacht = True
                        for m in range(N):
                            D1 = AAM.multVec(K2[m]["Direction"])
                            Match = False
                            for n in range(N):
                                D2 = K1[n]["Direction"]
                                
                                Angle = abs(D1.getAngle(D2))
                                if Angle < tol:
                                    Match = True
                                    # print(f"D1:{D1} \t D2:{D2}\t with {k}{i}{j}{l} Match:{Match}")
                                    break
                                # print(f"D1:{D1} \t D2:{D2} \t with {k}{i}{j}{l} Match:{Match}")
                            if Match is False:
                                allMacht = False
                                break

                        if allMacht is True:
                            Results.append(matrixToAxisAngle(AAM))

    return Results

#oreintations = FindallMatches4(Knot2,Knot1S5)
#print(oreintations)

def FindallMatches6(K1,K2,tol=1e-6):
    '''
    K1: Knot1 Stationary,
    K2: Knot2 gets Transformed
    description:
    Finds all the matches, where K2 gets Transformed into K1 successfully
    retrun: tuple((App.Vector,float),...)
    '''
    Results = []
    AllPairnigs = []
    N = len(K1)
    for k in range(N):
        B1 = K1[k]["Direction"]
        B1.normalize()
        for i in range(N):
            if k == i:
                continue
            B2 = K1[i]["Direction"]
            B2.normalize()
            for l in range(N):
                A1 = K2[l]["Direction"]
                A1.normalize()
                for m in range(N):
                    if l == m:
                        continue
                    A2 = K2[m]["Direction"]
                    A2.normalize()

                    # print(f"{k}{i}{l}{m}")
                    A1c,B1c,A2c,B2c = copyVec(A1),copyVec(B1),copyVec(A2),copyVec(B2)
                    # print(f"A1:{A1c} | B1:{B1c} | A2:{A2c} | B2:{B2c}")
                    HE1 = A1c-B1c
                    HE2 = A2c-B2c
                    axis = HE1.cross(HE2)
                    A1p =A1c.projectToPlane(App.Vector(0,0,0),axis)
                    B1p =B1c.projectToPlane(App.Vector(0,0,0),axis)
                    angle = math.degrees(A1p.getAngle(B1p))

                    print(f"axis:{axis} | angle:{angle} | HE1:{HE1} | HE2:{HE2}")

                    A = App.Rotation(axis,angle)

                    allMacht = True
                    Pairings = []
                    for o in range(N):
                        D1 = A.multVec(K2[o]["Direction"])
                        Match = False
                        for p in range(N):
                            D2 = K1[p]["Direction"]
                            Angle = abs(D1.getAngle(D2))
                            if Angle < tol:
                                Match = True
                                # Pairings.append((o,p))
                                Pairings.append((p))
                                print(f"D1:{D1} \t D2:{D2}\t with {k}{i}{l}{m} Match:{Match}")
                                break
                            # print(f"D1:{D1} \t D2:{D2} \t with {k}{i}{l}{m} Match:{Match}")
                            if Match is False:
                                allMacht = False
                                break

                        if allMacht is True:
                            AxisAngle = (axis,angle)
                            # print(A.decompose())
                            # print(AxisAngle)
                            if AxisAngle in Results:
                                rr = 1
                            elif Pairings in AllPairnigs:
                                rr = 2
                            else:
                                Results.append(AxisAngle)
                                AllPairnigs.append(Pairings)
                                #print(f"Appended Pairing:{Pairings}")
    print(AllPairnigs)
    return Results

# oreintations = FindallMatches6(Knot2,Knot1S1)
# print(len(oreintations))
# for o in oreintations:
#     print(o)


# N = 10
# li = list(range(N))
# # print(li)
# com = list(permutations(li,len(li)))
# l = len(com)

# for item in com:
#     print(item)

# print(l)

def FindallMatches2(K1,K2,tol=1e-6):
    '''
    K1: Knot1 Stationary,
    K2: Knot2 gets Transformed
    description:
    Finds all the matches, where K2 gets Transformed into K1 successfully
    retrun: tuple((App.Vector,float),...)
    '''
    Results = []
    AllPairnigs = []
    N = len(K1)
    for k in range(N):
        B1 = K1[k]["Direction"]
        for i in range(N):
            if k == i:
                continue
            B2 = K1[i]["Direction"]
            for l in range(N):
                A1 = K2[l]["Direction"]
                for m in range(N):
                    if l == m:
                        continue
                    A2 = K2[m]["Direction"]

                    B3 = B1.cross(B2)
                    A3 = A1.cross(A2)
                    # Matrizen V und W konstruieren
                    V = App.Base.Matrix()
                    V.setCol(0, B1)
                    V.setCol(1, B2)
                    V.setCol(2, B3)

                    W = App.Base.Matrix()
                    W.setCol(0, A1)
                    W.setCol(1, A2)
                    W.setCol(2, A3)

                    # Inverse von V berechnen
                    V_inv = V.inverse()

                    # Transformationsmatrix A = W * V_inv
                    A = W.multiply(V_inv)

                    allMacht = True
                    Pairings = []
                    for o in range(N):
                        D1 = A.multVec(K2[o]["Direction"])
                        Match = False
                        r = 0
                        for p in range(N):
                            D2 = K1[p]["Direction"]
                            Angle = abs(D1.getAngle(D2))
                            if Angle < tol:
                                Match = True
                                Pairings.append((o,p))
                                # Pairings.append((p))
                                # print(f"D1:{D1} \t D2:{D2}\t with {k}{i}{j}{m} Match:{Match}")
                                break
                            # print(f"D1:{D1} \t D2:{D2} \t with {k}{i}{l}{m} Match:{Match}")
                            r = r + 1
                        if Match is False:
                            allMacht = False
                            break

                        if allMacht is True:
                            AxisAngle = matrixToAxisAngle(A)
                            # print(A.decompose())
                            # print(AxisAngle)
                            if AxisAngle in Results:
                                rr = 1
                            elif Pairings in AllPairnigs:
                                rr = 2
                            else:
                                Results.append(AxisAngle)
                                AllPairnigs.append(Pairings)
                                # print(f"Appended Pairing:{Pairings}")
    print(AllPairnigs)
    # print(Results)
    return Results

# oreintations = FindallMatches2(Knot2,Knot1S1)
# print(len(oreintations))
# for o in oreintations:
#     print(o)