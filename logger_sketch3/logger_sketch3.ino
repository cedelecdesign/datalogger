/*

     _____         _        _           _                   _                _           _             
    / ____|       | |      | |         | |                 (_)              | |         (_)            
   | |     ___  __| |   ___| | ___  ___| |_ _ __ ___  _ __  _  ___ ___    __| | ___  ___ _  __ _ _ __  
   | |    / _ \/ _` |  / _ \ |/ _ \/ __| __| '__/ _ \| '_ \| |/ __/ __|  / _` |/ _ \/ __| |/ _` | '_ \ 
   | |___|  __/ (_| | |  __/ |  __/ (__| |_| | | (_) | | | | | (__\__ \ | (_| |  __/\__ \ | (_| | | | |
    \_____\___|\__,_|  \___|_|\___|\___|\__|_|  \___/|_| |_|_|\___|___/  \__,_|\___||___/_|\__, |_| |_|
                                                                                          __/ |      
                                                                                         |___/       
    Project     : Data logger
    File        : logger_Sketch.ino
    Version     : 1.0
    Description : Arduino and Processing based data logger
    
*/



const int analogPin = A0; // Analog pin
long delayTime = 1;     // Delay between readings
long multiplier = 1000;      // Used to calculate delay
String delayStr;          // Get delay from serial port commands
String delayTmpStr;
bool isRunning = false;

/*******************************
   Initialise
 ******************************/
void setup() {
  
  //Setup serial connection
  Serial.begin(57600);

  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
  
}

void setParams() {
  
  delayStr = Serial.readString();
  //Serial.println(delayStr);
  if(delayStr.charAt(delayStr.length()-1) == 'm'){
    multiplier = 1;
    setDelay();
  }else if(delayStr.charAt(delayStr.length()-1) == 's'){
    multiplier = 1000;
    setDelay();
  }else if(delayStr.charAt(delayStr.length()-1) == 'M'){
    multiplier = 60000;
    setDelay();
  }else if(delayStr.charAt(delayStr.length()-1) == 'R'){
    isRunning = true;
    return;
  }else if(delayStr.charAt(delayStr.length()-1) == 'C'){
    isRunning = false;
    return;
  }
  
}

void setDelay() {
  
  delayTmpStr = delayStr.substring(0, delayStr.length()-1);
  delayTime = long(delayTmpStr.toFloat());
  delayTime = delayTime * multiplier;
  
}

/*********************************
   Main loop
 ********************************/
void loop() {

  if(isRunning){
    // Read analog pin
    int val = analogRead(analogPin);
    // Write analog value to serial port: (send an int with 3 bytes)
//    Serial.write( 0xff );
//    Serial.write( (val >> 8) & 0xff );
//    Serial.write( val & 0xff );
    Serial.println(val);
    //delay betwwen two data transmission
    delay(delayTime);  
  }
  
  if(Serial.available() > 0) {
    setParams();
  }
  
  
}
