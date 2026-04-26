// 5-intersection rotation simulator using a single 3-LED signal head.
// Sequence: J1 -> J2 -> J3 -> J4 -> J5 -> repeat
// Per intersection timing: GREEN 3s, YELLOW 1s, RED 2s

void setup() {
  Serial.begin(115200);
  pinMode(2, OUTPUT);  // RED
  pinMode(3, OUTPUT);  // YELLOW
  pinMode(4, OUTPUT);  // GREEN

  setRed();
  Serial.println("Traffic controller started: 5-junction rotation mode");
}

const char* JUNCTIONS[] = {"J1", "J2", "J3", "J4", "J5"};
const int JUNCTION_COUNT = 5;

const unsigned long GREEN_MS = 3000;
const unsigned long YELLOW_MS = 1000;
const unsigned long RED_MS = 2000;

enum Phase {
  PHASE_GREEN,
  PHASE_YELLOW,
  PHASE_RED
};

int currentJunction = 0;
Phase currentPhase = PHASE_GREEN;
unsigned long phaseStartedAt = 0;

void clearAll() {
  digitalWrite(2, LOW);
  digitalWrite(3, LOW);
  digitalWrite(4, LOW);
}

void setRed() {
  clearAll();
  digitalWrite(2, HIGH);
}

void setYellow() {
  clearAll();
  digitalWrite(3, HIGH);
}

void setGreen() {
  clearAll();
  digitalWrite(4, HIGH);
}

void printState() {
  if (currentPhase == PHASE_GREEN) {
    Serial.print(JUNCTIONS[currentJunction]);
    Serial.println(" GREEN");
    return;
  }
  if (currentPhase == PHASE_YELLOW) {
    Serial.print(JUNCTIONS[currentJunction]);
    Serial.println(" YELLOW");
    return;
  }
  Serial.print(JUNCTIONS[currentJunction]);
  Serial.println(" RED");
}

void applyPhase() {
  if (currentPhase == PHASE_GREEN) {
    setGreen();
  } else if (currentPhase == PHASE_YELLOW) {
    setYellow();
  } else {
    setRed();
  }
  printState();
}

void loop() {
  unsigned long now = millis();

  if (phaseStartedAt == 0) {
    phaseStartedAt = now;
    currentPhase = PHASE_GREEN;
    applyPhase();
    return;
  }

  if (currentPhase == PHASE_GREEN && now - phaseStartedAt >= GREEN_MS) {
    currentPhase = PHASE_YELLOW;
    phaseStartedAt = now;
    applyPhase();
    return;
  }

  if (currentPhase == PHASE_YELLOW && now - phaseStartedAt >= YELLOW_MS) {
    currentPhase = PHASE_RED;
    phaseStartedAt = now;
    applyPhase();
    return;
  }

  if (currentPhase == PHASE_RED && now - phaseStartedAt >= RED_MS) {
    currentJunction = (currentJunction + 1) % JUNCTION_COUNT;
    currentPhase = PHASE_GREEN;
    phaseStartedAt = now;
    applyPhase();
  }
}
