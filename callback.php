<?php
$code = $_GET['code'] ?? 'コードが取得できませんでした';
?>
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>認証コード</title></head>
<body>
<h2>認証コード（コピーしてください）</h2>
<textarea style="width:100%;height:100px;font-size:14px;"><?= htmlspecialchars($code) ?></textarea>
</body>
</html>
