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
        
        self.chronoamp = chronoamp.chronoamp()
        self.lsv = lsv.lsv()
        self.cve = cv.cv()
        self.swv = swv.swv()
        self.dpv = dpv.dpv()
        self.acv = acv.acv()
        self.pde = pd.pd()
 
        #fill exp_section
        self.exp_section = self.builder.get_object('exp_section_box')
        self.containers = {'cae': self.chronoamp.builder.get_object(
                                                            'scrolledwindow1')}
        self.containers['lsv'] = self.lsv.builder.get_object('scrolledwindow1')
        self.containers['cve'] = self.cve.builder.get_object('scrolledwindow1')
        self.containers['swv'] = self.swv.builder.get_object('scrolledwindow1')
        self.containers['dpv'] = self.dpv.builder.get_object('scrolledwindow1')
        self.containers['acv'] = self.acv.builder.get_object('scrolledwindow1')
        self.containers['pde'] = self.pde.builder.get_object('scrolledwindow1')

        for key in self.containers:
            self.containers[key].reparent(self.exp_section)
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