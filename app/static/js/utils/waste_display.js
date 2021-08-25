Object.entries(waste).forEach(entry => createRow(entry[0], entry[1].bag_size, entry[1].material, entry[1].num_bags, false))

function createRow(rowId, bagSize, material, numBags, canDelete = true) {
    $('#bag-info-table')
        .find('tbody')
        .append(`
        <tr id="row_${rowId}">
            <td>${bagSize}</td>
            <td>${material}</td>
            <td>${numBags}</td>
            <td><button type="button" id="delete_row_${rowId}" class="btn btn-danger entry-delete-btn" ${canDelete ? "" : "hidden"}>Delete</button></td>
        </tr>`)
    $(`#delete_row_${rowId}`).click(_ => deleteRow(rowId))
}
