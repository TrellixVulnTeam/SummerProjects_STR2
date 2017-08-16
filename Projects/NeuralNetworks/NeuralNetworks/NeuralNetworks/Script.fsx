#I  "../packages/"  
#r "packages/MathNet.Numerics.3.19.0/lib/net40/MathNet.Numerics.dll"
#r "packages/MathNet.Numerics.FSharp.3.19.0/lib/net40/MathNet.Numerics.FSharp.dll"
open MathNet.Numerics
open MathNet.Numerics.LinearAlgebra  
open System 

let FLT_MAX = 1.0 //TODO: set this to correct value and probably move it to own file of parameters


type Output = {
    bias : Vector<float> ;
    SummedWeight : Vector<float>; 
    value:float ;
    output_size: float; 
}

let SENNA_nn_max input1 (output:Output)  = 
    let updatedoutput= 
        let  input = 
          if input1 >= 0.0  
          then (input1 + abs(input1) )/2.0 
          else 0.0
        {output with value = input}   
    updatedoutput 
            
let SENNA_nn_hardtanh input1 (output:Output) = 
    let updatedoutput  = 
        let input = 
            if input1>= -1.0 && input1<= 1.0
            then input1  
            elif input1< -1.0
            then -1.0 
            else  1.0
        {output with value = input} 
    updatedoutput 


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

let SENNA_nn_temporal_max (T:int)(N:int) (z:float) (input: array<float>)=
    let nList=[0..N]
    let combine list1=      
        seq {for t in 0..T do 
             yield! List.map (fun n -> (t,n)) list1 }
    let combinedList = combine nList 
    let zMatch ((t:int),(n:int)) =  
        if t*N+n-1< input.Length-1 && input.[t*N+n-1]>z GIVES INDEX DISPLAY ERROR, THOUGH INDEX SHOULD BE IN BOUNDS?
        then input.[t*N+n-1]
        else z
    let toList= Seq.toList combinedList 
    List.map zMatch toList 

//version 2
let SENNA_nn_temporal_max2 (output: array<float>) (input: array<float>) (N:int) (T:int)  =
    for n = 0 to N-1 do
        let mutable z = -FLT_MAX
        for t = 0 to T-1 do
            if input.[t*N+n] > z then
                z <- input.[t*N+n];
        output.[n] <- z


//let result = SENNA_nn_temporal_max 1 1 1.0 [|1.0 .. 50.0|]
let output = [|1.0 .. 50.0|]
let result = SENNA_nn_temporal_max2 output [|1.0 .. 50.0|] 3 3
output

let SENNA_nn_temporal_max_convolution
    (inp_f_size: int) 
    (k_w       : int  ) 
    (i         : int  )
    (j         : int  )
    (n_frames  : int  ) 
    (k         : int  ) 
    (bias      : array<float>) 
    (maxval    : float)
    (z         : array<float>)
    (input     : array<float>) 
    (output    : array<float>)     = 
    let jtoZ = 
        let jSeq =  
            seq { for j in -k..n_frames-k ->
                  let jFunc j = 
                     match j with
                     |j when j<0 -> 0
                     |j when j>=k_w -> k_w
                     |_ -> failwith "j out of bounds"
                  j   }
        let zElem= Seq.map (fun j -> i+j*inp_f_size) jSeq    
        let zArray elem = input.[elem] + bias.[elem] 
        let zCompile = Seq.map zArray zElem 
        let zCorrect z = 
            if z>maxval then maxval else z 
        let zCompile2 = Seq.toList(Seq.map zCorrect zCompile) 
        zCompile2 


    let combine  list2=      
        seq {for t in 0..inp_f_size  do 
             yield! List.map (fun n -> (t,n)) list2 }
    let addListtoPairwiseElem x = fun x ->  
    let nFramesList=[0..n_frames]

    let combinedList = Seq.toList (combine nFramesList) 
    let finalCombinedList= Seq.toList (combine2 combinedList) 
    printfn "%A" finalCombinedList


//#define NN_MIN(a,b) ((a) < (b) ? (a) : (b))
//#define NN_MAX(a,b) ((a) > (b) ? (a) : (b))

let NN_MIN a b =
    if a < b then
        a
    else
        b