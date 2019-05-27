

route_dictionary = {
    #straight routes
    ('Road1', 'Road2_out') : 12, #up to down
    ('Road2', 'Road1_out') : 21, #down to up
    ('Road3', 'Road4_out') : 34, #right to left
    ('Road4', 'Road3_out') : 43, #left to right
    #turning routes
    ('Road4', 'Road1_out') : 41, #left to up
    ('Road4', 'Road2_out') : 42, #left to down
    ('Road3', 'Road2_out') : 32, #right to down
    ('Road3', 'Road1_out') : 31, #right to up
    ('Road2', 'Road4_out') : 24, #down to left
    ('Road2', 'Road3_out') : 23, #down to right
    ('Road1', 'Road3_out') : 13, #up to right
    ('Road1', 'Road4_out') : 14  #up to left
}
