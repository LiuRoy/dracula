struct aaa {
    1: i32 a1,
    2: string a2,
}

struct bbb {
    1: double b1,
    2: list<string> b2;
    3: map<string, aaa> b3;
}


service TestService {
  string get_md5(1:string input_str, 2:bbb input_struct);
}
