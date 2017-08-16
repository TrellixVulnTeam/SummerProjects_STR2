#r "packages/MathNet.Numerics.3.19.0/lib/net40/MathNet.Numerics.dll"
#r "packages/MathNet.Numerics.FSharp.3.19.0/lib/net40/MathNet.Numerics.FSharp.dll"
open MathNet.Numerics
open MathNet.Numerics.LinearAlgebra  
open System 

let FLT_MAX = 1.0 //TODO: set this to correct value and probably move it to own file of parameters
         
// max(0,x) function
let SENNA_nn_max (input:array<float>)(size: int)=
    let  maxFn elem = 
          if elem >= 0.0  
          then elem  
          else 0.0
    let shortenedInput = Array.sub input 0 size 
    let output= Array.map maxFn shortenedInput 
    output 

// hardtanh function       
let  SENNA_nn_hardtanh (input:array<float>) (size:int) =  
    if size > input.Length-1 then failwith "Size of output too large" else
    let hardtanhFn elem =
        if elem>= -1.0 && elem<= 1.0
        then elem 
        elif elem < -1.0
        then -1.0
        else 1.0 
    let shortenedInput = Array.sub input 0 size 
    let output = Array.map hardtanhFn shortenedInput  
    output  

 
let SENNA_nn_temporal_max (output: array<float>) (input: array<float>) (N:int) (T:int)  =
    if (N*N+T) > (input.Length-1) || (N*N+T) > (output.Length-1) then failwith "Index specifications falls out of bounds: Make:N,T smaller"
    else 
    for n = 0 to N-1 do
        let mutable z = -FLT_MAX
        for t = 0 to T-1 do
        if input.[t*N+n] > z  
        then z <- input.[t*N+n]
        output.[n] <- z
        printfn "output = %A" output 

SENNA_nn_temporal_max [|0.0 .. 50.0|] [|0.0 .. 50.0|] 5 5  

// v2. v1 creates multiple output arrays dependent on input of n and t 
// v2 creates a single output array. output = (output value, (T,N))

let SENNA_nn_temporal_max2  (input: array<float>) (N:int) (T:int)  =
    if (N*N+T) > (input.Length-1) then failwith "Index specifications falls out of bounds: Make N,T smaller"
    else
    let z = -FLT_MAX
    let createTuplesFn (list1: list<int>)(list2:list<int>) = 
        seq {for t in 0..List.head(List.rev(list1))  do 
             yield! List.map (fun n -> (t,n)) list2 }
    let createTuplesArray = Seq.toArray (createTuplesFn [0..T-1] [0 .. N-1])
    let indexCorrectFn (n,t)  = 
        if input.[t*N+n] > z  
        then input.[t*N+n]
        else z 
    let indexCorrect = Array.map indexCorrectFn createTuplesArray 
    let output = Array.zip indexCorrect createTuplesArray 
    printfn "output = %A" output 
       
SENNA_nn_temporal_max2 [|0.0 .. 50.0|] 5 5  


 

         
type LookupVector = {
      i:int ;
      dest:float ;  
      dest_stride:int ;  
      wordweights: float ;  
      wordsize:int ; 
      maxwordidx:int ; 
      wordindices: int ; 
      nword : int   ; 
      padidx:int  ; 
      npad: int  ; 
}

let SENNA_nn_WordIndex_Lookup (lookup:LookupVector) = 
    seq {for i in 0..lookup.nword do 
          yield vector[
           (lookup.dest+float lookup.i+ float lookup.npad)*(float lookup.dest_stride) ;
            lookup.wordweights+(float lookup.i)*(float lookup.wordsize); 
            (float lookup.wordsize* (float sizeof<float>))]
        }

let SENNA_nn_Padding_Lookup (lookup:LookupVector) = 
    seq {for i in 0..lookup.npad do 
          yield vector[
           (float lookup.dest) + (float lookup.i* float lookup.dest_stride); 
           lookup.wordweights+(float lookup.padidx)*(float lookup.wordsize); 
           (float lookup.wordsize* (float sizeof<float>))] 
    }

let SENNA_nn_Padding_Lookup2 (lookup:LookupVector) = 
    seq {for i in 0..lookup.npad do 
          yield vector[
           (float lookup.dest)+(float lookup.i+float lookup.npad+float lookup.nword)*float lookup.dest_stride; 
           lookup.wordweights+(float lookup.padidx) *(float lookup.wordsize); 
           (float lookup.wordsize* (float sizeof<float>))] }


//let SENNA_nn_temporal_max (input: array<float>) (N:int) (T:int) (z:float)=
    //let nList=[0..N-1]
    //let combine list1=      
    //    seq {for t in 0..T-1 do 
    //         yield! List.map (fun n -> (t,n)) list1 }
    //let combinedList = combine nList 
    //let zMatch ((t:int),(n:int)) =  
    //    if t*N+n< input.Length && input.[t*N+n]>z 
    //    then input.[t*N+n]
    //    else z
    //let toList= Seq.toList combinedList 
    //List.map zMatch toList 




//let SENNA_nn_temporal_max_convolution
//    (inp_f_size: int) 
//    (k_w       : int  ) 
//    (i         : int  )
//    (j         : int  )
//    (n_frames  : int  ) 
//    (k         : int  ) 
//    (maxval    : float)
//    (bias      : array<float>) 
//    (z         : array<float>)
//    (input     : array<float>) 
//    (output    : array<float>)     = 
//    let jtoZ = 
//        let jSeq =  
//            seq { for j in float -k.. float n_frames- float k ->
//                  let jFunc j = 
//                     match j with
//                     |j when j<0 -> 0
//                     |j when j>=k_w -> k_w
//                     |_ -> failwith "j out of bounds"
//                  j   }
//        let zElem= Seq.map (fun j -> (float i)+j* (float inp_f_size)) jSeq    
//        let zElemCorrect (elem:float )=
//            if   elem>(float (input.Length-1)) || elem> (float (bias.Length-1))
//            then input.[input.Length-1]  
//            else elem  
//        let zCompile = Seq.map zElemCorrect zElem 
//        let zCorrect z = 
//            if z>maxval then maxval else z 
//        let zCompile2 = Seq.toList(Seq.map zCorrect zCompile) 
//        zCompile2 


//    let combine  list2=      
//        seq {for t in 0..inp_f_size  do 
//             yield! List.map (fun n -> (t,n)) list2 }
//    let combine2  list2=      
//        seq {for n in 0..n_frames  do 
//             yield! List.map (fun (t,u) -> (t,u,n)) list2 } 
//    let combinedList1 = Seq.toList (combine jtoZ) 
//    let combinedList2 = Seq.toList (combine2 combinedList1) 
//    printfn "%A" combinedList2


//SENNA_nn_temporal_max_convolution 49 49 49 49 49 49 49.0 [|1.0 .. 50.0 |] [|1.0 .. 25.0 |] [|1.0 .. 50.0 |] [|1.0 .. 50.0 |]

////#define NN_MIN(a,b) ((a) < (b) ? (a) : (b))

//let NN_MIN a b =
//    if a < b then
//        a
//    else
//        b
////#define NN_MAX(a,b) ((a) > (b) ? (a) : (b)

//v 2 
//let  SENNA_nn_hardtanh2 (output: array<float>) (input:array<float>) (size:int) =  
    //if size > input.Length-1 then failwith "Size of output too large" else
    //let hardtanhFn i = 
    //    let mutable z = input.[i]
    //    if z < -1.0
    //    then z <- -1.0
    //    elif z > 1.0
    //    then  1.0 
    //    output.[i] = z
    //let result= Array.map hardtanhFn output 
    //printfn "ouptut= %A" result 
//let SENNA_nn_max2 
    //(value_:array<float>)
    //(idx_:array<int>)
    //(input:array<float>)
    //(input_size: int)=
    //let value = -FLT_MAX 
    //let idx = -1 
    //let mutable i = 0 
    //let  maxFn elem = 
    //      if elem >= 0.0  
    //      then elem  
    //      else 0.0
    //let shortenedInput = Array.sub input 0 input_size 
    //let output= Array.map maxFn shortenedInput 
    //output 






