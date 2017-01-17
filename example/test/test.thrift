struct aaa {
    1: i32 a1,
    2: string a2,
}

struct bbb {
    1: double b1,
    2: list<string> b2,
    3: map< string, aaa > b3,
    4: list<aaa> b4,
    5: map<string, list<aaa> > b5,
    6: list< list<aaa> > b6,
}


service TestService {
  string test(1:string input_str, 2:bbb input_struct);
}
