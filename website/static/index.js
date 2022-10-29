function deleteNote(noteId) {
    fetch('/delete-note', {
        method: 'POST', 
        body: JSON.stringify({noteId: noteId}), 
    }).then((_res) => {
        window.location.href = "/"; 
    });
}


function deleteSim(simId) {
    fetch('/delete-sim', {
        method: 'POST', 
        body: JSON.stringify({simId: simId}), 
    }).then((_res) => {
        window.location.href = "/"; 
    });
}

function exportTableToExcel(tableID, filename = ''){
    var downloadLink;
    var dataType = 'application/vnd.ms-excel';
    var tableSelect = document.getElementById(tableID);
    var tableHTML = tableSelect.outerHTML.replace(/ /g, '%20');
    
    // Specify file name
    filename = filename?filename+'.xls':'excel_data.xls';
    
    // Create download link element
    downloadLink = document.createElement("a");
    
    document.body.appendChild(downloadLink);
    
    if(navigator.msSaveOrOpenBlob){
        var blob = new Blob(['\ufeff', tableHTML], {
            type: dataType
        });
        navigator.msSaveOrOpenBlob( blob, filename);
    }else{
        // Create a link to the file
        downloadLink.href = 'data:' + dataType + ', ' + tableHTML;
    
        // Setting the file name
        downloadLink.download = filename;
        
        //triggering the function
        downloadLink.click();
    }
}