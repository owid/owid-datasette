const copyToClipboard = async (text) => {
  await navigator.clipboard.writeText(text);
};

const addCopyButtonToCell = (cell, value) => {
  const copyButton = document.createElement("button");
  copyButton.className = "owid-copy-button fa fa-copy";
  copyButton.onclick = () => copyToClipboard(value);
  cell.append(copyButton);
};

const cells = document.querySelectorAll("table.rows-and-columns td");
cells.forEach((cell) => {
  const value = cell.innerText;

  addCopyButtonToCell(cell, value);
});
