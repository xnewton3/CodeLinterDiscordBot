<?php

// PHP Novice → 2.Fruity Loops → 4.Piramide
$rows  = readline('Hoeveel stapels wil je hebben? ');
$current = 1;

while ($current <= $rows) {
    $spaces = $rows - $current; 
    $output = str_repeat("  ", $spaces);

    $stars = (2 * $current) - 1;
    $output .= str_repeat("* ", $stars); 

// Print it
    echo $output . PHP_EOL;

    $current++;
}

?>