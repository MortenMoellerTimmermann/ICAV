//This file was generated from (Commercial) UPPAAL 4.0.14 (rev. 5615), May 2014

/*

*/
strategy GoSafe =minE (SoftCrashDetected) [<=300] : <> CrashDetector.CrashDetected == 0
/*

*/
strategy GoFast =maxE (totalSpeed) [<=300] : <> forall (i:carID) Cars(i).End under GoSafe
/*

*/
simulate 1 [<=300] {  Cars(0).newSpeed, Cars(1).newSpeed, Cars(2).newSpeed, Cars(3).newSpeed , SoftCrashDetected } under GoFast



//E<> CrashDetector.CrashDetected == 0 and forall (i:carID) Car(i).End