test_file = open('studentdata.txt', 'r')


lines = test_file.readline()
while lines:

    reformated = lines.split()
    min_value = 100
    max_value = 0 
    
 
    for i in reformated[1:]:
	numb = int(i)
        if numb < min_value: 
            min_value = numb 

        elif i > max_value:
            max_value = i 
        
        
    print(reformated[0], 'has an max score of', max_value, 'and a min score of', min_value)
        
    lines = test_file.readline()
    


test_file.close()
