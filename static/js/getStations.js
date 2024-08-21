async function getStation(){
    let res = await fetch("/api/mrt/name",{
        "Content-type":"application/json"
    });
    let result = await res.json();
    // console.log(result);
    return result;
}
export  {getStation};

