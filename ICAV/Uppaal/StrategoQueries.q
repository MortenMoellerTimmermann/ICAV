//This file was generated from (Commercial) UPPAAL 4.0.14 (rev. 5615), May 2014

/*

*/
strategy GoSafe = control: A[] not(CrashDetector.CrashDetected > 0) 
/*

*/
strategy GoFast =maxE (totalSpeed) [<=300] : <> forall (i:carID) Cars(i).End under GoSafe
/*

*/
simulate 1 [<=300] { /*HOLDER_CAR_QUERY*/ , SoftCrashDetected, CrashDetector.CrashDetected } under GoFast




//E<> CrashDetector.CrashDetected == 0 and forall (i:carID) Cars(i).End
//strategy GoSafe =minE (SoftCrashDetected) [<=300] : <> CrashDetector.CrashDetected == 0
