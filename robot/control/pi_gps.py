import gps
import logging
import json

class Pi_GPS:
    def __init__(self,conf):
        # Listen on port 2947 (gpsd) of localhost
        self.session = gps.gps("localhost", "2947")
        self.session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

        logging.basicConfig(filename=conf['log_path'], filemode='a',
        format=conf['log_format'], level=logging.getLevelName(conf['log_level']))
    
    def report_loop(self):
        while True:
            try:
                report = self.session.next()
                # print(report)
                if report['class'] == 'TPV':
                    if hasattr(report, 'time'):
                        logging.debug(report.time)
                    if all(hasattr(report, attr) for attr in ['lon','lat']):
                        logging.debug(f"{report.lat}, {report.lon}")
                    else:
                        logging.warning("No connected")
            except KeyError:
                pass
            except KeyboardInterrupt:
                quit()
            except StopIteration:
                self.session = None
                logging.warning("GPSD has terminated")
    
    def get_location(self):
        data = {'connected': False}
        if self.session is not None:
            while True:
                try:
                    report = self.session.next()
                    logging.debug(report)
                    if report['class'] == 'TPV':
                        # if hasattr(report, 'time'):
                        #     print(report.time)
                        if all(hasattr(report, attr) for attr in ['lon','lat','speed']):
                            logging.debug(f"{report.lat}, {report.lon}")
                            data =  {
                                'connected': True, 
                                'latitude': report.lat, 
                                'longitude': report.lon,
                                'speed': report.speed
                            }
                            if hasattr(report, 'track'):
                                data['heading'] = report.track
                        else:
                            logging.warning("Not connected")
                        
                        break
                    
                except KeyError:
                    pass
                except StopIteration:
                    self.session = None
                    logging.warning("GPSD has terminated")
        return data

if __name__ == '__main__':
    with open("robocam_conf.json") as f:
        conf = json.load(f)
    g = Pi_GPS(conf)
    # g.report_loop()
    print(g.get_location())