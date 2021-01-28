/****************************** EE3 Remap Group Project ********************************/
/* This open-source code realizes basic control theory to a two-wheel drived
 * wheelchair using a two-axis joystick input, enabling several advanced features.
 *
 *************************************** NOTICE *****************************************
 * WHEN COMPILING AND UPLOADING THE PROGRAM TO ARDUINO, ANY CONNECTIONS TO DIGITAL
 * PIN 1(RX) SHOULD BE REMOVED TO PREVENT THE UPLOADING PROGRESS BEING STUCKED.
 *
 * This program initially runs at Arduino Uno, due to lack of pins, the three pins for
 * buttons are assigned to be analog pins instead of digital pins due to lack of digital
 * I/O pins on the board.
 *
 * If "serial_display" is turned on, the digital pin 0 and 1 would be unusable.
 */

// These libraries are necessary when using nRF8001 Bluetooth module
#include <SPI.h>
#include "Adafruit_BLE_UART.h"
// The link to download "Adafruit_BLE_UART.h" library is:
// https://github.com/adafruit/Adafruit_nRF8001/archive/master.zip


/*********************************** Pin Assignment ************************************/
#define x_channel A0        // input analogue pin for reading joystick input
#define y_channel A1        // input analogue pin for reading joystick input
#define PWM_left 6          // output digital pin (PWM) for controlling left motor
#define PWM_right 5         // output digital pin (PWM) for controlling left motor
#define rev_left1 7          // pin number for reverse (FW) of left motor
#define rev_left2 8
#define rev_right1 3        // pin number for reverse (FW) of right motor
#define rev_right2 4         // pin number for reverse (FW) of right motor

#define stby A2



/*************************** Parameters Settings for Tuning ****************************/
#define ttl_max 1           // (0~1) maximum standardized throttle for each motor
#define ttld_ratio 0.3      // (0~1) ratio of differential to max throttle
#define ttl_left_gain 1     // (>0) additional gain for left motor, default = 1
#define ttl_right_gain 1    // (>0) additional gain for right motor, default = 1
#define t_stat_max 1        // (>=0) delay of braking after stationary (in second)
#define update_freq 20      // (Hz) frequency that the program updates PWM and reads input
#define serial_display 1    // (1 = on, 0 = off) whether display info through serial port
                            // default = 0, since digital pins 0 and 1 are used

#define x_inverted 1        // (-1 or 1) -1 = inverted, 1 = non-inverted
#define y_inverted 1        // (-1 or 1) -1 = inverted, 1 = non-inverted

#define x_linearity 1       // (>0) linearity, default = 1 (linear)
#define x_sensitivity 1     // (>0) sensitivity/overall gain, default = 1
#define x_deadzone 0.1      // (0~1) due to non-zero inaccuracy of the joystick

#define y_linearity 1       // (>0) linearity, default = 1 (linear)
#define y_sensitivity 1     // (>0) sensitivity/overall gain, default = 1
#define y_deadzone 0.1      // (0~1) due to non-zero inaccuracy of the joystick

#define js_limit 0.4        // limit of change per second in ttls (sync jerk)
#define jd_limit 0.5        // limit of change per second in ttld (diff jerk)


/***************** Other Parameters Settings and Variables Declarations ****************/
#define ADAFRUITBLE_RDY 2   // This should be an interrupt pin, on Uno thats #2 or #3
#define ADAFRUITBLE_RST A1   // connects to SPI Chip Select pin, can be changed to any pin
#define ADAFRUITBLE_REQ 10  // resets the board when start up, can be changed to any pin

double ttls_max = ttl_max*(1-ttld_ratio);   // maximum synchronized throttle
double ttld_max = ttl_max*ttld_ratio;       // maximum differential throttle

double ttls_out = 0;        // output synchronized throttle
double ttld_out = 0;        // output differential throttle
double t_stat = 0;          // stopwatch in EABS, time since stationary
int stat = 0;               // stationary flag (0 = moving, 1 = stationary)
int brakes = 1;             // (1 = on, 0 = off), brakes for both wheels, default = 1

int but1 = 0, but1_1 = 0;   // (0,1) initial button 1 value and delayed value
int but2 = 0, but2_1 = 0;   // (0,1) initial button 2 value and delayed value
int but3 = 0, but3_1 = 0;   // (0,1) initial button 3 value and delayed value

int jlmt_ctrl = 1;          // (1 = on, 0 = off), Jerk Limiter switch, default = 1
int crs_ctrl = 0;           // (1 = on, 0 = off), cruise control switch, default = 0
int eabs_ctrl = 1;          // (1 = on, 0 = off), EABS switch, default = 1
double ttls_crs = 0;        // cruise control throttle value

int jx_sign, jy_sign;
double jx, jy, jx_adj, jy_adj;
double ttls_ref, ttld_ref, dttls, dttld, ttl_left, ttl_right, dttls_max, dttld_max;
double T = 1000/update_freq;    // (in ms) convert update frequency into time period
double dt, t_tmp;
unsigned long t_start, t_end;   // start and stop time for the stopwatch

String message_x = "";
String message_y = "";
boolean comma = false;
boolean inputData = false;
boolean reading = true;

// Extract the sign of a value
template <typename T> int sign(T val) {
    return (val>T(0))-(val<T(0));
}

Adafruit_BLE_UART BTLEserial = Adafruit_BLE_UART(ADAFRUITBLE_REQ, ADAFRUITBLE_RDY, ADAFRUITBLE_RST);

void display_info();

void setup() {
    // assign left and right motor direction and digital PWM pins to be output pins
    pinMode(rev_left1, OUTPUT);
    pinMode(rev_right1, OUTPUT);
    pinMode(rev_left2, OUTPUT);
    pinMode(rev_right2, OUTPUT);
    pinMode(PWM_left, OUTPUT);
    pinMode(PWM_right, OUTPUT);
    pinMode(stby, OUTPUT);

    if(serial_display == 1){
        // Inizialize Serial
        Serial.begin(9600);
    }

    analogWrite(stby, 255);

    BTLEserial.begin();
}
aci_evt_opcode_t laststatus = ACI_EVT_DISCONNECTED;


/************************************* Main Loop ***************************************/
void loop(){
    // measure the time consumed for current literation
    t_end = millis();
    dt = t_end-t_start;
    t_tmp = T-dt;
    if(t_tmp > 0){
        delay(t_tmp);
        dt = T/1000;
    }else dt = dt/1000;
    t_start = millis();

    // Store previous button values
    but1_1 = but1;
    but2_1 = but2;
    but3_1 = but3;


    /************************** Read Joystick Input Data ******************************/
    // Tell the nRF8001 to do whatever it should be working on
    BTLEserial.pollACI();

    // Ask what is our current status
    aci_evt_opcode_t status = BTLEserial.getState();

    // If the status changed....
    if (status != laststatus){
        if(serial_display == 1){
            // print it out!
            if (status == ACI_EVT_DEVICE_STARTED){
                Serial.println(F("* Advertising started"));
            }
            if (status == ACI_EVT_CONNECTED){
                Serial.println(F("* Connected!"));
            }
            if (status == ACI_EVT_DISCONNECTED){
                Serial.println(F("* Disconnected or advertising timed out"));
            }
        }
        // set the last status change to this one
        laststatus = status;
    }

    // Read joystick and button data from app
    if(status == ACI_EVT_CONNECTED){

            comma = false;
            message_x = "";
            message_y = "";
            while(BTLEserial.available()){
                inputData = true;
                char c = BTLEserial.read();
                // Serial.print(c);
                if(c == ',') comma = true;
                if(c != ',' && comma == false) message_x.concat(c);
                if(c != ',' && comma == true) message_y.concat(c);
                if(c == 'D'){
                    if(serial_display == 1) Serial.println(c);
                    reading = false;
                }

                if(c == 'C'){       // Cruise Control
                    if(serial_display == 1) Serial.println(c);
                    but1 = 1;
                    ttls_crs = 0.6; // set cruise ttls 60% if using joystick in app
                }
                else but1 = 0;

                if(c == 'B'){       // EABS
                    if(serial_display == 1) Serial.println(c);
                    but3 = 1;
                }
                else but3 = 0;

                if(c == 'J'){       // Jerk Limiter
                    if(serial_display == 1) Serial.println(c);
                    but2 = 1;
                }
                else but2 = 0;
            }

            if(inputData == true){
                jx = message_x.toDouble()/100;
                jy = message_y.toDouble()/100;
                inputData = false;
            }


        if(reading == false){
            //String s = getData();
            //uint8_t sendbuffer[20];
            //s.getBytes(sendbuffer, 20);
            //char sendbuffersize = min(20, s.length());

            if(serial_display == 1){
                Serial.println("Writing!");
                Serial.print(F("\n* Sending -> \""));
                //Serial.print((char *)sendbuffer);
                Serial.println("\"");
            }
            //BTLEserial.write(sendbuffer, sendbuffersize);
        }
    }

    // Read joystick and button data from physical joystick and buttons
    else{

        // convert jx an jy into the range -1~1
        jx = 0;
        jy = 0;

        // convert analog value into digital value
        but1 = 0;
        but2 = 0;
        but3 = 0;
    }


    /***************************** Adjust Joystick Data *******************************/
    // extract the sign of joystick data for both axes
    jx_sign = sign(jx);
    jy_sign = sign(jy);

    if(abs(jx) < x_deadzone) jx_adj = 0;    // eliminate x-axis deadzone
    else{
        // x-axis adjustments
        jx_adj = (abs(jx)-x_deadzone)/(1-x_deadzone);
        jx_adj = pow(x_sensitivity*jx_sign*jx_adj, x_linearity);
        jx_adj = max(min(jx_adj, 1), -1);   // limit jx value whithin -1~1
    }

    if(abs(jy) < y_deadzone) jy_adj = 0;    // eliminate y-axis deadzone
    else{
        // y-axis adjustments
        jy_adj = (abs(jy)-jy_sign*y_deadzone)/(1-y_deadzone);
        jy_adj = pow(y_sensitivity*jy_sign*jy_adj, y_linearity);
        jy_adj = max(min(jy_adj, 1), -1);   // limit jy value whithin -1~1
    }


    /********************** Calculate Reference Throttle Values ***********************/
    // throttle of left wheel motor before smoothing:
    ttl_left = jy_adj*ttls_max + jx_adj*ttld_max;
    // throttle of right wheel motor before smoothing:
    ttl_right = jy_adj*ttls_max - jx_adj*ttld_max;

    ttls_ref = (ttl_left+ttl_right)/2;    // convert to synchronized throttle
    ttld_ref = (ttl_left-ttl_right)/2;    // convert to differential throttle


    /********************************* Jerk Limiter ***********************************/
    dttls_max = js_limit*dt;    // maximum change in synchronized throttle
    dttld_max = jd_limit*dt;    // maximum change in differential throttle

    if(but2 > but2_1){          // when Jerk Limiter button is pressed
        jlmt_ctrl = 1 - jlmt_ctrl;      // toggle Jerk Limiter switch
    }

    if(jlmt_ctrl == 1){
        dttld = ttld_ref-ttld_out;    // change in diff throttle
        dttld = max(min(dttld, dttld_max), -dttld_max);   // capping
        ttld_out = ttld_out+dttld;    // output diff throttle

        dttls = ttls_ref-ttls_out;    // change in sync throttle
        dttls = max(min(dttls, dttls_max), -dttls_max);   // capping
        ttls_out = ttls_out+dttls;    // output sync throttle
    }
    else{
        // no change
        ttld_out = ttld_ref;
        ttls_out = ttls_ref;
    }


    /**************************** Cruise Control System *******************************/
    // detect whether cruise control button is pressed and toggle if so
    if(but1 > but1_1){
        if((crs_ctrl == 0) && (ttls_out > 0)){
            crs_ctrl = 1;           // off -> on

            // get current sync ttl value if using physical joystick
            if(ttls_crs == 0) ttls_crs = ttls_out;
        }
        else{
            crs_ctrl = 0;           // on -> off
            ttls_crs = 0;           // clear sync ttl value
        }
    }

    if(crs_ctrl == 1){
        if(ttls_ref >= 0){          // only when moving forward
            ttls_out = ttls_crs;    // replace output sync ttl value
        }
        else{                       // cancel if moving backward
            crs_ctrl = 0;           // cancel cruise control
            ttls_crs = 0;           // clear sync ttl value
        }
    }


    /************************* Electronic Auto-Braking System *************************/
    if(but3 > but3_1){   // when EABS button is pressed
        eabs_ctrl = 1 - eabs_ctrl;        // toggle switch
        if(eabs_ctrl == 0) brakes = 0;    // brakes disengaged
    }

    // time since stationary
    if((ttls_out == 0) && (ttld_out == 0)){
        if(stat == 0){
            t_stat = t_stat + dt;     // start stopwatch and accumulate dt
            if(t_stat >= t_stat_max) stat = 1;    // is t_stat seconds after stationary
        }
    }
    else{
        stat = 0;     // reset flag
        t_stat = 0;   // reset stopwatch
    }

    if(eabs_ctrl == 1){
        // Brakes are on after t_stat_max seconds since no output throttles
        if(stat == 1)   brakes = 1;     // brakes engaged
        else            brakes = 0;     // brakes disengaged
    }


    /************** Calculate Left and Right Throttle and Output to Pins **************/
    // update throttle of left wheel motor after smoothing
    ttl_left = (ttls_out + ttld_out)*ttl_left_gain;
    // update throttle of right wheel motor after smoothing
    ttl_right = (ttls_out - ttld_out)*ttl_right_gain;

    // decide directions of motor rotations (send to FW pins in motor controllers)
    if(ttl_left >= 0)   {digitalWrite(rev_left2, LOW); digitalWrite(rev_left1, HIGH);}
    else                {digitalWrite(rev_left2, HIGH); digitalWrite(rev_left1, LOW);}
    if(ttl_right >= 0)  {digitalWrite(rev_right2, LOW); digitalWrite(rev_right1, HIGH);}
    else                {digitalWrite(rev_right2, HIGH); digitalWrite(rev_right1, LOW);}

    // convert throttle values to PWM signals, LED signals and send to pins
    analogWrite(PWM_left, abs(ttl_left)*255);     // PWM of left wheel
    analogWrite(PWM_right, abs(ttl_right)*255);   // PWM of right wheel


    // Display Infomation
    if(serial_display == 1) display_info();
}


void display_info(){
    // Display some information through serial port the more info displayed
    // the slower the program will be, and pin 0 and 1 would be unusable
    String str = "";
    str = String(dt,3) + " "+String(ttl_left) + " "+String(ttl_right);
    str += " "+String(jx) + " "+String(jy);
    Serial.println(str);
}

String getData(){
    return "1";
}
