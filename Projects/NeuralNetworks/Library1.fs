namespace Senna_Stuff
open MathNet.Numerics.LinearAlgebra
open MathNet.Numerics 

type Output = {
    bias : Vector<float> ;
    SummedWeight : Vector <float>; 
    input: float ;
    value:float ;
    output_size: float; 
}

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

module SENNA_nn_Functions = 
    open MathNet.Numerics 
    open MathNet.Numerics.LinearAlgebra 

    let NewOutput = {
        bias = vector[0.0] ; 
        SummedWeight = vector[0.0]   ; 
        input= 0.0 ;  
        value= 0.0 ; 
        output_size= 0.0;    
    }


    let SENNA_nn_max input1 (output:Output)  = 
        let updatedoutput= 
            let  input = 
              if input1 >= 0.0  
              then (input1 + abs(input1) )/2.0 
              else 0.0
            {output with value = input}   
        updatedoutput 
    
        
    let SENNA_nn_hardtanh input (output:Output) = 
        let updatedoutput  = 
            let input1 = 
                if input>= -1.0 && input<= 1.0
                then input  
                elif input< -1.0
                then -1.0 
                else  1.0
            {output with value = input1} 
        updatedoutput 


    let SENNA_nn_WordIndex_Lookup (lookup:LookupVector) = 
        for i in 0..lookup.nword do 
            let wordIDvector= vector[(lookup.dest+float lookup.i+ float lookup.npad)*(float lookup.dest_stride) ;
            lookup.wordweights+(float lookup.i)*(float lookup.wordsize); (float lookup.wordsize* (float sizeof<float>))]
            wordIDvector

    let SENNA_nn_Padding_Lookup (lookup:LookupVector) = 
        for i in 0..lookup.npad do 
            let paddingvector= vector[(float lookup.dest) + (float lookup.i* float lookup.dest_stride); 
            lookup.wordweights+(float lookup.padidx)*(float lookup.wordsize); (float lookup.wordsize* (float sizeof<float>))] 
            paddingvector

    let SENNA_nn_Padding_Lookup2 (lookup:LookupVector) = 
        for i in 0..lookup.npad do
            let secondpaddingvector = vector[(float lookup.dest)+(float lookup.i+float lookup.npad+float lookup.nword)*float lookup.dest_stride; 
            lookup.wordweights+(float lookup.padidx) *(float lookup.wordsize); (float lookup.wordsize* (float sizeof<float>))]
            secondpaddingvector 
