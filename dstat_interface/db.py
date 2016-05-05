import logging
from time import sleep, time
from os.path import expanduser
from uuid import uuid4

from BTrees.OOBTree import OOBTree

import mr_db.mr_db as db

logger = logging.getLogger("dstat.db")

current_db = None

def start_db(path=None):
    global current_db
    current_db = Database(data_dir=path)

def restart_db(object, path):
    logger.info("Restarting database")
    global current_db
    if current_db is None:
        logger.info("No database running")
        start_db(path=path)
    else:
        stop_db()
        start_db(path=path)

def stop_db():
    global current_db
    if not current_db is None:
        logger.info("Stopping ZEO")
        current_db.disconnect()
        current_db = None
        db.stop_server()
    else:
        logger.warning("Tried to disconnect ZEO when not connected")

class Database(object):
    def __init__(self, name='dstat', data_dir=None):
        if data_dir is None:
            data_dir = expanduser('~/.mr_db')
        self.connected = False
        self.name = name
        
        self.db_connect(data_dir)
        
        self.db = self.connection.databases
        
        # Make sure database exists
        if not self.db.has_key(name):
            self.db[name] = OOBTree()
            db.transaction.commit()
    
    def disconnect(self):
        if self.connected is True:
            self.connection.db.close()
        else:
            logger.war("Tried to disconnect ZEO when not connected")
    
    def db_connect(self, root_dir):
        """Connects to ZEO process. Starts ZEO if not running. Returns 
        connection object.
        """
        if root_dir == '':
            root_dir = None
        
        while self.connected is False:
            try:
                self.connection = db.DbConnection(root_dir=root_dir)
                self.connected = True
                logger.info("Connected to ZEO server")
            except db.ClientStorage.ClientDisconnected:
                db.stop_server()
                logger.info("Starting ZEO server -- root_dir = %s", root_dir)
                db_proc = db.start_server(root_dir=root_dir)
                sleep(3)
    
    def add_results(self, measurement_uuid=None, measurement_name=None,
                    experiment_uuid=None, experiment_metadata=None,
                    patient_id=None,
                    timestamp=None,
                    data=None):
                    
        """Add a measurement"""
        
        if experiment_metadata is None:
            experiment_metadata = {}
            
        try:
            logger.info("Starting DB transaction")
            db.transaction.begin()
            
            logger.info("Creating Experiment with id: %s", experiment_uuid)
            exp_db, exp_id = self.add_experiment(
                                    experiment_uuid=experiment_uuid,
                                    timestamp=timestamp,
                                    **experiment_metadata)

            logger.info("Adding Measurement with id: %s", measurement_uuid)
            name = self.add_dstat_measurement(experiment=exp_db[exp_id],
                                       measurement_uuid=measurement_uuid,
                                       name=measurement_name,
                                       timestamp=timestamp,
                                       data=data)
        
            if patient_id is not None:
                if not patient_id in self.db['patients']:
                    logger.info("Creating patient with id: %s", patient_id)
                    patient = db.Patient(pid=patient_id)
                    self.db['patients'][patient_id] = patient
                
                if not exp_id in self.db['patients'][patient_id].experiments:
                    logger.info("Linking experiment into patient with id: %s",
                                patient_id)    
                    self.db['patients'][patient_id].link_experiment(exp_db,
                                                                    exp_id)
                
            logger.info("Committing DB transaction")
            db.transaction.commit()
            
            return name
        
        except:
            logger.error("Aborting DB transaction")
            db.transaction.abort()
            raise
      
    def add_experiment(self, experiment_uuid=None, timestamp=None, **kwargs):
        """Add a new experiment. Will raise KeyExistsError if id is already
        in db to avoid unintended collisions.
        ----
        Arguments:
        id: experiment id---UUID will be generated if not supplied
        timestamp: current time---Will be generated if not supplied
        kwargs: additional keyword arguments that will be saved in experiment.
        """
    
        if experiment_uuid is None:
            experiment_uuid = uuid4().hex
        if timestamp is None:
            timestamp = time()
        
        kwargs.update({'id':experiment_uuid, 'timestamp':timestamp})
         
        if not experiment_uuid in self.db[self.name]:
            self.db[self.name][experiment_uuid] = db.PersistentMapping()
        else:
            logger.info("Experiment already exists, appending")
        
        self.db[self.name][experiment_uuid].update(kwargs)
        
        return (self.db[self.name], experiment_uuid)
        
    def add_dstat_measurement(self, experiment, measurement_uuid=None,  
                              data=None, timestamp=None, name=None):
                              
        if measurement_uuid is None:
            measurement_uuid = uuid4().hex
        if timestamp is None:
            timestamp = time()
        if data is None:
            data = {}
        
        if not 'measurements' in experiment:
            experiment['measurements'] = db.PersistentMapping()
        if not 'measurements_by_name' in experiment:
            experiment['measurements_by_name'] = db.PersistentMapping()
        
        if measurement_uuid in experiment['measurements']:
            raise db.KeyExistsError(measurement_uuid,
                "Measurement ID already exists. Access directly to update")
        
        data['timestamp'] = timestamp
        data['id'] = measurement_uuid
        
        if name is not None:
            data['name'] = name
        
        experiment['measurements'][measurement_uuid] = data
        
        if name is not None:
            while name in experiment['measurements_by_name']:
                first, sep, last = name.rpartition('-')
                
                if last.isdigit():
                    index = int(last)
                    index += 1
                    name = sep.join((first,str(index)))
                else:
                   name += '-1' 
                   
            experiment['measurements_by_name'][name] = data
            
        return name