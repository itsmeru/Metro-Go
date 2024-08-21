async function getTicket(position){
    let res = await fetch(`/api/mrt/ticket/${position}`,{
        "Content-type":"application/json"
    });
    let result = await res.json();
    return result;
}
export  {getTicket};
