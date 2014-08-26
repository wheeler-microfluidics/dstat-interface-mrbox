import interface.exp_int as exp

class Experiments:
    def __init__(self, builder):
        self.builder = builder
        
        self.classes = {}
        self.classes['cae'] = exp.Chronoamp()
        self.classes['lsv'] = exp.LSV()
        self.classes['cve'] = exp.CV()
        self.classes['swv'] = exp.SWV()
        self.classes['dpv'] = exp.DPV()
        self.classes['acv'] = exp.ACV()
        self.classes['pde'] = exp.PD()
 
        #fill exp_section
        exp_section = self.builder.get_object('exp_section_box')
        self.containers = {}
        
        for key, cls in self.classes.iteritems():
            self.containers[key] = cls.builder.get_object('scrolledwindow1')

        for key in self.containers:
            self.containers[key].reparent(exp_section)
            self.containers[key].hide()
            
        
    def set_exp(self, selection):
        """Changes parameter tab to selected experiment. Returns True if 
        successful, False if invalid selection received.
        
        Arguments:
        selection -- id string of experiment type
        """
        for key in self.containers:
            self.containers[key].hide()

        self.containers[selection].show()
        
        return True
        
    def get_params(self, experiment):
        return self.classes[experiment].get_params()