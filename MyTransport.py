#my run a basic simulation 


class MySim:
    Source = None
    Elemets = None
    BeamMatrix =[]

    # defenition of electrostatic QP with 1st order and ds
    def AddQP(self, QP= {},type='E', order = 1, ds = 0):
        HalfApp = QP['HalfApature']
        PoleR = 1.147 * poleRpos
        poleLen = QP['Len[m]']
        if(type=='E'):
            Volts = QP['Volts']
            k_val = 0
        else:
            Field = QP['Feild[kG]']

        if(order==1):
