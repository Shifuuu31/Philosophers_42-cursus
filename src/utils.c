/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   utils.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: asaadane <asaadane@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/01/02 23:04:06 by asaadane          #+#    #+#             */
/*   Updated: 2026/11/18 19:43:00 by asaadane         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "philo.h"

// Check whitespaces
static int	escape_whitespaces(char c)
{
	if (c == 32 || c == '\t' || c == '\v'
		|| c == '\f' || c == '\r' || c == '\n')
		return (1);
	return (0);
}

// Check if character is a digit
int	ft_isdigit(int c)
{
	return (c >= '0' && c <= '9');
}

// Custom atoi function to convert string to integer
int	ft_atoi(const char *str)
{
	long long	res;
	int			j;
	int			sign;

	j = 0;
	res = 0;
	sign = 1;
	while (escape_whitespaces(str[j]))
		j++;
	if (str[j] == '+' || str[j] == '-')
	{
		if (str[j] == '-')
			sign *= -1;
		j++;
	}
	while (ft_isdigit(str[j]))
	{
		res = (res * 10) + (str[j] - '0');
		if (res > 2147483647)
			return (-1);
		j++;
	}
	return ((int)(res * sign));
}

// Custom usleep function to pause execution for a specified duration
void	ft_usleep(unsigned long long time)
{
	unsigned long long	sleep_time;

	sleep_time = ft_time();
	while (ft_time() - sleep_time < time)
		usleep(100);
}

// Pause execution until an exact wall-clock target timestamp is reached
void	ft_usleep_until(long long target)
{
	while (ft_time() < target)
		usleep(100);
}

// Get current timestamp in milliseconds
long long	ft_time(void)
{
	struct timeval	timestamp;

	gettimeofday(&timestamp, NULL);
	return ((timestamp.tv_sec * 1000) + (timestamp.tv_usec / 1000));
}
