# Wikipedia Quiz
## 想定ユーザー
クイズを楽しみたい人

## 目的
クイズが無限に出題される

## 機能
クイズとヒントが出てきて、正解、不正解を判定する  
ヒントは記事の後半部分から抜粋し、答えを文字数分の○○に置換している

## 実装
1. WikipediaのAPIからrandomに記事を取得  
2. 記事の長さによって最大５回のチャンス  
（ヒントとして記事が８０文字ずつ出てくる）  
3. 一度回答が始まるとuseridと記事id，ヒント回数をcsv(s3に保存)に書き込み

` 授業で作りました。`
## 参考画像
<img src="https://user-images.githubusercontent.com/65396705/170175550-9eeec211-e5d5-43fe-802c-8716bcf19df4.png" width="33%"><img src="https://user-images.githubusercontent.com/65396705/170175562-bce241cb-c06d-40d5-b641-7978760664bc.png" width="33%"><img src="https://user-images.githubusercontent.com/65396705/170175568-f2d4114b-db7e-4e01-b307-5d85faa4d4b2.png" width="33%">

## 仕組み
![image](https://user-images.githubusercontent.com/65396705/170175574-5df4336d-0d3a-41c6-b838-40fc7426bdd0.png)

初めてAWSを使いました。CloudWatchなどでlogを見ながらやるのは普通のﾌﾟﾛｸﾞﾗﾐﾝｸﾞと変わらないと思いました。