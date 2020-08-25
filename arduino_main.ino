const int outputPin = 3;
const int inputPin = 2;
const int buttonPin = 4;
const int ledPin = 5;

int pulse_on = 0;
int pulse_delta = 0;
int numberofstimuli = 0;
int predelay = 0;


int buttonState = HIGH;
int inputState = LOW;
int start_pulse = false;

int counter = 0;
int everything_armed = 0;

//serial communication functions marginally adapted 
//from forum.arduino.cc user Robin2
//see https://forum.arduino.cc/index.php?topic=271097.0
//and https://forum.arduino.cc/index.php?topic=396450

const byte numChars = 32;
char receivedChars[numChars];
char tempChars[numChars]; 
boolean newData = false;
boolean readInProgress = false;
byte bytesRecvd = 0;
unsigned long curMillis;
unsigned long prevReplyToPCmillis = 0;
unsigned long replyToPCinterval = 1000;

void setup() {
  Serial.begin(9600); // Öffnet die serielle Schnittstelle bei 9600 Bit/s:
  Serial.println("<Arduino is ready>");
  
  pinMode(outputPin, OUTPUT);
  pinMode(inputPin, INPUT);
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(ledPin, OUTPUT);

  digitalWrite(outputPin, LOW);
  digitalWrite(ledPin, LOW);
}

void loop() {
  curMillis = millis();
   recvWithStartEndMarkers();
   if (newData == true) {
       strcpy(tempChars, receivedChars);
           // this temporary copy is necessary to protect the original data
           //   because strtok() used in parseData() replaces the commas with \0
       parseData();
       //showParsedData();
       newData = false;
   }
  if(everything_armed == 1){
  input_check();
  button_check();
  predelay_check();
  do_pulse();
  }
  sendToPC();

}

void predelay_check(){
  if(predelay != 0){
    if(start_pulse == true && counter == 0){
      delay(predelay);
    }
  }
}
void do_pulse(){
  
  if(start_pulse == true && counter < numberofstimuli) {
    counter++;
    
    digitalWrite(outputPin, HIGH);
    digitalWrite(ledPin, HIGH);
    delay(pulse_on);
    digitalWrite(outputPin, LOW);
    digitalWrite(ledPin, LOW);
    delay(pulse_delta);
    
   } 
  else if(counter >= numberofstimuli){
    counter = 0;
    start_pulse = false;
  }
}

void input_check(){
  inputState = digitalRead(inputPin);
  if(inputState == HIGH){
  start_pulse = true;
  }
}

void button_check(){
  buttonState = digitalRead(buttonPin);
  if(buttonState == LOW){
  //Serial.print(buttonState);
  start_pulse = true;
  }
}
void recvWithStartEndMarkers() {
    static boolean recvInProgress = false;
    static byte ndx = 0;
    char startMarker = '<';
    char endMarker = '>';
    char rc;

    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();

        if (recvInProgress == true) {
            if (rc != endMarker) {
                receivedChars[ndx] = rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                }
            }
            else {
                receivedChars[ndx] = '\0'; // terminate the string
                recvInProgress = false;
                ndx = 0;
                newData = true;
            }
        }

        else if (rc == startMarker) {
            recvInProgress = true;
        }
    }
}

//============

void parseData() {      // split the data into its parts

    char * strtokIndx; // this is used by strtok() as an index

    strtokIndx = strtok(tempChars,",");      // get the first part - the string
    pulse_on = atoi(strtokIndx);     // convert this part to an integer
 
    strtokIndx = strtok(NULL, ","); // this continues where the previous call left off
    pulse_delta = atoi(strtokIndx);     // convert this part to an integer

    strtokIndx = strtok(NULL, ",");
    numberofstimuli = atoi(strtokIndx);    

    strtokIndx = strtok(NULL, ",");
    predelay = atoi(strtokIndx);     
    
    strtokIndx = strtok(NULL, ",");
    everything_armed = atoi(strtokIndx);     

}

//============

void showParsedData() {
    Serial.print("Pulse on: ");
    Serial.println(pulse_on);
    Serial.print("Pulse delay: ");
    Serial.println(pulse_delta);
    Serial.print("Number of stimuli: ");
    Serial.println(numberofstimuli);
    Serial.print("Predelay: ");
    Serial.println(predelay);
    Serial.print("Everything armed:: ");
    Serial.println(everything_armed);
}

void sendToPC() {
  if (curMillis - prevReplyToPCmillis >= replyToPCinterval) {
    prevReplyToPCmillis += replyToPCinterval;
    Serial.print('<');
    Serial.print("Arduino is ready");
    Serial.print('>');
  }
  
}
