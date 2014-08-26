import chronoamp
import lsv
import cv
import swv
import dpv
import acv
import pd

class Experiments:
    def __init__(self, builder):
        self.builder = builder
        
        self.classes = {}
        self.classes['cae'] = chronoamp.Chronoamp()
        self.classes['lsv'] = lsv.lsv()
        self.classes['cve'] = cv.cv()
        self.classes['swv'] = swv.swv()
        self.classes['dpv'] = dpv.dpv()
        self.classes['acv'] = acv.acv()
        self.classes['pde'] = pd.pd()
 
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
        