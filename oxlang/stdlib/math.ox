//
//  math.ox
//  Ox Standard Library
//  (From Cub Standard Library)
//

/// The mathematical constant pi.
pi = 3.14159265358979

/// The mathematical constant tau, which equals 2*pi.
tau = pi * 2

/// - Parameter x: A number.
/// - Returns: The absolute value of x.
func abs(x) {
	if x < 0 {
		return x * -1
	}
	
	return x
}

/// - Parameter a: A number to compare.
/// - Parameter b: Another number to compare.
/// - Returns: The lesser of a and b.
func min(a, b) {
	if a < b {
		return a
	}
	
	return b
}

/// - Parameter a: A number to compare.
/// - Parameter b: Another number to compare.
/// - Returns: The greater of a and b.
func max(a, b) {
	if a > b {
		return a
	}
	
	return b
}

/// - Parameter x: a number.
/// - Returns: wether x is positive.
func isPositive(x) {
	return x > 0
}

/// - Parameter x: a number.
/// - Returns: wether x is negative.
func isNegative(x) {
	return x < 0
}

/// - Parameter x: a number.
/// - Returns: wether x is even.
func isEven(x) {
	return mod(x, 2) == 0
}

/// - Parameter x: a number.
/// - Returns: wether x is uneven.
func isUneven(x) {
	return !isEven(x)
}

/// - Parameter n: the root.
/// - Parameter x: a number.
/// - Returns: the n-root of x.
func root(n, x) {
	return x ^ (1 / n)
}

/// - Parameter x: a number.
/// - Returns: the square root of x.
func sqrt(x) {
	return root(2, x)
}

/// - Parameter x: a number.
/// - Returns: the cube root of x.
func cbrt(x) {
	return root(3, x)
}

/// - Parameter x: dividend
/// - Parameter y: divisor
/// - Returns: remainder
func rem(x, y) {
	
	y = abs(y)
	
	if isPositive(x) {
		
		while x >= y {
			x -= y
		}
		
	} else {
		
		while x <= (-1 * y) {
			x += y
		}
		
	}
	
	return x
}

/// - Parameter x: dividend
/// - Parameter y: divisor
/// - Returns: modulus
func mod(x, y) {
	
	if y == 0 || abs(y) > abs(x) {
		return x
	}
	
	y = abs(y)
	
	if isPositive(x) {
		
		while x >= y {
			x -= y
		}
		
	} else {
		
		while x <= y {
			if x >= 0 {
				break
			}
			
			x += y
		}
		
	}
	
	return x
}

/// - Parameter x: a number.
/// - Returns: the greatest whole number less than x.
func floor(x) {
	return x - mod(x, 1)
}

//func ceil(x) {
//	// TODO
//	return x
//}

/// - Parameter x: a number.
/// - Returns: the rounded value of x
func round(x) {
	
	// TODO: fix for negative numbers!
	// e.g. round(-2.423) should give -2
	
	if x < 0.0 {
		return floor(x - 0.5)
	} else {
		return floor(x + 0.5)
	}
}
